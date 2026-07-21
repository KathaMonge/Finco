import asyncio
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from services.ocr.engine import run_ocr
from services.ocr.layout_analyzer import analyze_layout
from services.ocr.models import OCRResult
from services.ocr.pdf_converter import pdf_to_images
from services.ocr.preprocessor import preprocess_image
from services.ocr.parsers.registry import ParserRegistry
from utils.threading import OCR_EXECUTOR

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}


class OCRService:
    async def process(self, file_path: str | Path) -> OCRResult:
        """Process an image or PDF file and extract financial data.

        Runs in a thread executor to avoid blocking the Flet event loop.
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            OCR_EXECUTOR,
            self._process_sync,
            str(file_path),
        )
        return result

    def _process_sync(self, file_path: str) -> OCRResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {extension}. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        if extension == ".pdf":
            images = pdf_to_images(path)
            if not images:
                raise ValueError("PDF has no pages")
            image = images[0]
            logger.info(f"Using first page of PDF ({len(images)} total pages)")
        else:
            image = Image.open(path)

        processed = preprocess_image(image)
        detections = run_ocr(processed)
        lines = analyze_layout(detections)

        emisor = ParserRegistry.detect_emisor(lines)
        parser = ParserRegistry.get_parser(emisor)
        result = parser.parse(lines)
        result.raw_lines = lines

        logger.info(
            f"OCR complete: emisor={result.emisor}, "
            f"confidence={result.overall_confidence:.2f}, "
            f"fields={sum(1 for f in [result.monto, result.fecha, result.comercio, result.tarjeta] if f)}"
        )
        return result


ocr_service = OCRService()
