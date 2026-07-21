import cv2
import numpy as np
from PIL import Image


def preprocess_image(image: Image.Image, max_height: int = 1200) -> Image.Image:
    """Apply OpenCV preprocessing to improve OCR accuracy."""
    img_array = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    denoised = cv2.fastNlMeansDenoising(gray, h=30)

    deskewed = _deskew(denoised)

    thresh = cv2.adaptiveThreshold(
        deskewed,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2,
    )

    h, w = thresh.shape
    if h > max_height:
        scale = max_height / h
        new_w = int(w * scale)
        thresh = cv2.resize(thresh, (new_w, max_height), interpolation=cv2.INTER_AREA)

    return Image.fromarray(thresh)


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct image rotation/skew."""
    coords = np.column_stack(np.where(image > 0))
    if len(coords) == 0:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    elif angle > 45:
        angle = angle - 90

    if abs(angle) < 0.5:
        return image

    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated
