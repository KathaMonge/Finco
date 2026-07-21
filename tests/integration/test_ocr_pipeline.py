"""Integration tests for the full OCR pipeline.

These tests require sample receipt images in assets/sample_receipts/.
They are skipped if no sample images are present.
"""

from pathlib import Path

import pytest

from services.ocr.ocr_service import ocr_service
from services.ocr.preprocessor import preprocess_image
from services.ocr.pdf_converter import pdf_to_images
from services.ocr.layout_analyzer import analyze_layout


SAMPLE_DIR = Path("assets/sample_receipts")
SAMPLE_IMAGES = list(SAMPLE_DIR.glob("*.jpg")) + list(SAMPLE_DIR.glob("*.png"))
SAMPLE_PDFS = list(SAMPLE_DIR.glob("*.pdf"))


def _has_samples():
    return len(SAMPLE_IMAGES) > 0 or len(SAMPLE_PDFS) > 0


@pytest.mark.skipif(not _has_samples(), reason="No sample receipts found")
class TestOCRPipeline:
    async def test_process_image(self):
        result = await ocr_service.process(str(SAMPLE_IMAGES[0]))
        assert result.raw_lines is not None
        assert len(result.raw_lines) > 0

    def test_preprocessor(self):
        from PIL import Image
        img = Image.open(SAMPLE_IMAGES[0])
        processed = preprocess_image(img)
        assert processed is not None
        assert processed.mode == "L"

    def test_layout_analyzer(self):
        detections = [
            {"bbox": [[0, 0], [50, 0], [50, 20], [0, 20]], "text": "Hello", "confidence": 0.95},
            {"bbox": [[0, 25], [60, 25], [60, 45], [0, 45]], "text": "World", "confidence": 0.90},
        ]
        lines = analyze_layout(detections)
        assert len(lines) == 2
        assert lines[0] == "Hello"
        assert lines[1] == "World"


@pytest.mark.skipif(not SAMPLE_PDFS, reason="No sample PDFs found")
class TestPDFConverter:
    def test_pdf_to_images(self):
        images = pdf_to_images(SAMPLE_PDFS[0], dpi=200)
        assert len(images) > 0
        assert images[0].mode == "RGB"
