import logging

from PIL import Image

from services.ocr.onnx_engine import run_ocr_onnx

logger = logging.getLogger(__name__)


def run_ocr(image: Image.Image) -> list[dict]:
    """Run OCR on a PIL Image using ONNX Runtime (PP-OCRv3)."""
    return run_ocr_onnx(image)
