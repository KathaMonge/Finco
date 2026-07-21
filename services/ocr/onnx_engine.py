"""ONNX Runtime OCR engine using PP-OCRv6 models.

Replaces PaddleOCR with a lightweight ONNX Runtime backend.
Models auto-downloaded from HuggingFace on first use (~132MB total).
"""

import logging
import urllib.request
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import onnxruntime
import yaml
from PIL import Image

from core.config import USER_DATA_DIR

logger = logging.getLogger(__name__)

MODELS_DIR = USER_DATA_DIR / "models"
HF_BASE = "https://huggingface.co/PaddlePaddle"
MODEL_FILES = {
    "det": f"{HF_BASE}/PP-OCRv6_medium_det_onnx/resolve/main/inference.onnx",
    "rec": f"{HF_BASE}/PP-OCRv6_medium_rec_onnx/resolve/main/inference.onnx",
    "yml": f"{HF_BASE}/PP-OCRv6_medium_rec_onnx/resolve/main/inference.yml",
}


def _download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1024:
        return
    logger.info(f"Downloading {url} -> {dest}")
    urllib.request.urlretrieve(url, dest)
    if dest.stat().st_size < 1024:
        raise RuntimeError(f"Downloaded file too small ({dest.stat().st_size} bytes): {dest.name}")
    logger.info(f"Downloaded {dest.name} ({dest.stat().st_size / 1024 / 1024:.1f}MB)")


def _load_charset() -> list[str]:
    yml_path = MODELS_DIR / "inference.yml"
    _download(MODEL_FILES["yml"], yml_path)
    with open(yml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    chars = cfg["PostProcess"]["character_dict"]
    return ["<blank>"] + list(chars)


class ONNXEngine:
    def __init__(self):
        self._det: Optional[onnxruntime.InferenceSession] = None
        self._rec: Optional[onnxruntime.InferenceSession] = None
        self._charset: list[str] = []
        self._ready = False

    def initialize(self):
        if self._ready:
            return
        logger.info("Initializing ONNX OCR engine...")
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        det_path = MODELS_DIR / "ppocrv6_det.onnx"
        rec_path = MODELS_DIR / "ppocrv6_rec.onnx"

        _download(MODEL_FILES["det"], det_path)
        _download(MODEL_FILES["rec"], rec_path)
        self._charset = _load_charset()

        opts = onnxruntime.SessionOptions()
        opts.log_severity_level = 3
        self._det = onnxruntime.InferenceSession(str(det_path), opts, providers=["CPUExecutionProvider"])
        self._rec = onnxruntime.InferenceSession(str(rec_path), opts, providers=["CPUExecutionProvider"])
        self._ready = True
        logger.info(f"ONNX OCR engine ready (charset: {len(self._charset)} chars)")

    def run(self, image: np.ndarray) -> list[dict]:
        self.initialize()
        boxes = self._detect(image)
        results = []
        for box in boxes:
            crop = self._crop(image, box)
            text, conf = self._recognize(crop)
            results.append({"bbox": box, "text": text, "confidence": conf})
        results.sort(key=lambda r: (r["bbox"][0][1], r["bbox"][0][0]))
        return results

    def _detect(self, img: np.ndarray) -> list[np.ndarray]:
        h, w = img.shape[:2]
        resized = self._resize_det(img, 960)
        rh, rw = resized.shape[:2]

        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(1, 1, 3)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(1, 1, 3)
        inp = (resized.astype(np.float32) / 255.0 - mean) / std
        inp = np.transpose(inp, (2, 0, 1))[np.newaxis, :, :, :].astype(np.float32)

        det_out = self._det.run(None, {"x": inp})
        if not det_out:
            return []
        out = det_out[0]
        prob = 1.0 / (1.0 + np.exp(-out[0, 0, :, :]))

        boxes = self._db_postprocess(prob, rh, rw)
        for b in boxes:
            b[:, 0] *= w / rw
            b[:, 1] *= h / rh
        return boxes

    def _resize_det(self, img: np.ndarray, target: int = 960) -> np.ndarray:
        h, w = img.shape[:2]
        scale = target / max(h, w) if max(h, w) > target else 1
        nw = max(int(w * scale // 32 * 32), 32)
        nh = max(int(h * scale // 32 * 32), 32)
        return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)

    def _db_postprocess(self, prob: np.ndarray, oh: int, ow: int, thr: float = 0.65) -> list[np.ndarray]:
        binary = (prob > thr).astype(np.uint8)
        binary = cv2.resize(binary, (ow, oh), interpolation=cv2.INTER_NEAREST)
        binary = (binary > 0).astype(np.uint8)

        contours, _ = cv2.findContours(binary * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for cnt in contours:
            if cv2.contourArea(cnt) < 50:
                continue
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = self._unclip(box, 2.0)
            if cv2.contourArea(box) < 50:
                continue
            box = self._order_box(box)
            boxes.append(box)
        return boxes

    def _unclip(self, box: np.ndarray, ratio: float = 2.0) -> np.ndarray:
        area = cv2.contourArea(box)
        peri = cv2.arcLength(box, True)
        if peri < 1e-6:
            return box
        dist = area * ratio / max(peri, 1e-6)
        offsets = np.array([[-dist, -dist], [dist, -dist], [dist, dist], [-dist, dist]], dtype=np.float32)
        return box + offsets

    def _order_box(self, box: np.ndarray) -> np.ndarray:
        box = box.reshape(4, 2)
        s = box.sum(axis=1)
        d = np.diff(box, axis=1)
        ordered = np.zeros((4, 2), dtype=np.float32)
        ordered[0] = box[np.argmin(s)]
        ordered[2] = box[np.argmax(s)]
        ordered[1] = box[np.argmin(d)]
        ordered[3] = box[np.argmax(d)]
        return ordered

    def _crop(self, img: np.ndarray, box: np.ndarray) -> np.ndarray:
        box = box.astype(np.int32)
        w = max(int(np.linalg.norm(box[1] - box[0])), 1)
        h = max(int(np.linalg.norm(box[3] - box[0])), 1)
        dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
        M = cv2.getPerspectiveTransform(box.astype(np.float32), dst)
        return cv2.warpAffine(img, M[:2], (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    def _recognize(self, img: np.ndarray) -> tuple[str, float]:
        h, w = img.shape[:2]
        target_h = 48
        ratio = target_h / max(h, 1)
        nw = max(int(w * ratio), 16)
        resized = cv2.resize(img, (nw, target_h), interpolation=cv2.INTER_LINEAR)

        inp = resized.astype(np.float32) / 255.0
        mean = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 1, 3)
        std = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 1, 3)
        inp = (inp - mean) / std
        inp = np.transpose(inp, (2, 0, 1))[np.newaxis, :, :, :].astype(np.float32)

        rec_out = self._rec.run(None, {"x": inp})
        if not rec_out:
            return ("", 0.0)
        out = rec_out[0]
        return self._ctc_decode(out[0])

    def _ctc_decode(self, probs: np.ndarray) -> tuple[str, float]:
        preds = probs.argmax(axis=1)
        chars = []
        confs = []
        vocab = len(self._charset)
        prev = -1
        for i, idx in enumerate(preds):
            idx_i = int(idx)
            if idx_i == prev or idx_i == 0 or idx_i >= vocab:
                prev = idx_i
                continue
            chars.append(self._charset[idx_i])
            confs.append(float(probs[i, idx_i]))
            prev = idx_i
        text = "".join(chars)
        avg = sum(confs) / len(confs) if confs else 0.0
        return text, avg


_engine = None


def get_onnx_engine() -> ONNXEngine:
    global _engine
    if _engine is None:
        _engine = ONNXEngine()
    return _engine


def run_ocr_onnx(image: Image.Image) -> list[dict]:
    return get_onnx_engine().run(np.array(image.convert("RGB")))
