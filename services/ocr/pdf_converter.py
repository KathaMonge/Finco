import logging
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: Path, dpi: int = 300) -> list[Image.Image]:
    """Convert PDF pages to PIL Images using pdf2image."""
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(str(pdf_path), dpi=dpi)
        logger.info(f"Converted {len(images)} pages from {pdf_path.name}")
        return images
    except ImportError:
        logger.error(
            "pdf2image not available. Install: pip install pdf2image"
        )
        raise
    except Exception as e:
        logger.error(f"Failed to convert PDF {pdf_path}: {e}")
        raise
