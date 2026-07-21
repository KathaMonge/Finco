import re

from services.ocr.models import ExtractedField, OCRResult
from services.ocr.parsers.base import BaseParser
from services.ocr.parsers.registry import ParserRegistry
from utils.helpers import parse_amount, parse_date


@ParserRegistry.register("visa")
class VisaParser(BaseParser):
    DETECT_PATTERNS = [
        re.compile(r"vis[aá]", re.IGNORECASE),
        re.compile(r"cr[eé]dito\s+visa", re.IGNORECASE),
        re.compile(r"titular:\s*\w+", re.IGNORECASE),
    ]

    AMOUNT_PATTERNS = [
        re.compile(r"(?:total|consumo|pago)\s*:?\s*\$?\s*([\d.,]+)", re.IGNORECASE),
        re.compile(r"\$?\s*([\d.,]+)\s*\(?total\)?", re.IGNORECASE),
    ]

    DATE_PATTERNS = [
        re.compile(r"(?:fecha|emi[sú]i[oó]n)\s*:?\s*(\d{2}[/-]\d{2}[/-]\d{2,4})", re.IGNORECASE),
        re.compile(r"(\d{2}[/-]\d{2}[/-]\d{4})"),
    ]

    MERCHANT_PATTERNS = [
        re.compile(r"(?:comercio|establecimiento|proveedor)\s*:?\s*(.+)", re.IGNORECASE),
    ]

    CARD_PATTERNS = [
        re.compile(r"(?:tarjeta|nro|n[uú]mero|card)\s*:?\s*[\*x\s]*(\d{4})", re.IGNORECASE),
    ]

    def detect(self, lines: list[str]) -> bool:
        text = " ".join(lines).lower()
        return any(p.search(text) for p in self.DETECT_PATTERNS)

    def parse(self, lines: list[str]) -> OCRResult:
        result = OCRResult(emisor="visa", raw_lines=lines)

        full_text = " ".join(lines)

        for pattern in self.AMOUNT_PATTERNS:
            match = pattern.search(full_text)
            if match:
                amount = parse_amount(match.group(1))
                if amount:
                    result.monto = ExtractedField(
                        value=str(amount),
                        confidence=0.9,
                        raw_text=match.group(0),
                    )
                    break

        for pattern in self.DATE_PATTERNS:
            match = pattern.search(full_text)
            if match:
                parsed = parse_date(match.group(1))
                if parsed:
                    result.fecha = ExtractedField(
                        value=parsed.isoformat(),
                        confidence=0.85,
                        raw_text=match.group(0),
                    )
                    break

        for pattern in self.MERCHANT_PATTERNS:
            match = pattern.search(full_text)
            if match:
                merchant = match.group(1).strip().rstrip(".")
                result.comercio = ExtractedField(
                    value=merchant,
                    confidence=0.8,
                    raw_text=match.group(0),
                )
                break

        for pattern in self.CARD_PATTERNS:
            match = pattern.search(full_text)
            if match:
                result.tarjeta = ExtractedField(
                    value=match.group(1),
                    confidence=0.9,
                    raw_text=match.group(0),
                )
                break

        confs = [
            result.monto.confidence if result.monto else 0,
            result.fecha.confidence if result.fecha else 0,
        ]
        result.overall_confidence = sum(confs) / len(confs) if confs else 0.0
        return result
