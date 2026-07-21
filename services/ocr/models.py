from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class ExtractedField:
    value: str
    confidence: float
    raw_text: str
    method: str = "regex"

    @property
    def confidence_label(self) -> str:
        if self.confidence >= 0.9:
            return "high"
        elif self.confidence >= 0.7:
            return "medium"
        return "low"


@dataclass
class ExtractedTransaction:
    """A single transaction extracted from OCR (one row in a bank statement)."""
    amount: Decimal
    date: Optional[date] = None
    description: str = ""
    confidence: float = 0.5
    raw_text: str = ""


@dataclass
class OCRResult:
    emisor: str = "unknown"
    monto: Optional[ExtractedField] = None
    fecha: Optional[ExtractedField] = None
    comercio: Optional[ExtractedField] = None
    tarjeta: Optional[ExtractedField] = None
    items: list[ExtractedField] = field(default_factory=list)
    transactions: list[ExtractedTransaction] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)
    overall_confidence: float = 0.0
