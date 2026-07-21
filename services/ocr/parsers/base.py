from abc import ABC, abstractmethod

from services.ocr.models import OCRResult


class BaseParser(ABC):
    @abstractmethod
    def detect(self, lines: list[str]) -> bool:
        """Returns True if this parser can handle the given text."""
        ...

    @abstractmethod
    def parse(self, lines: list[str]) -> OCRResult:
        """Extract fields from OCR text lines."""
        ...
