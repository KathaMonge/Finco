import re

from services.ocr.models import ExtractedField, OCRResult
from services.ocr.parsers.base import BaseParser
from services.ocr.parsers.registry import ParserRegistry
from utils.helpers import parse_amount, parse_date


@ParserRegistry.register("amex")
class AmexParser(BaseParser):
    DETECT_PATTERNS = [
        re.compile(r"american\s+express", re.IGNORECASE),
        re.compile(r"\bamex\b", re.IGNORECASE),
        re.compile(r"axp", re.IGNORECASE),
    ]

    AMOUNT_PATTERNS = [
        re.compile(r"(?:total|amount|charge)\s*:?\s*\$?\s*([\d.,]+)", re.IGNORECASE),
        re.compile(r"\$?\s*([\d.,]+)\s*(?:usd|ars)?$", re.MULTILINE),
    ]

    DATE_PATTERNS = [
        re.compile(r"(?:date|fecha)\s*:?\s*(\d{2}[/-]\d{2}[/-]\d{2,4})", re.IGNORECASE),
        re.compile(r"(\d{2}/\d{2}/\d{4})"),
    ]

    def detect(self, lines: list[str]) -> bool:
        text = " ".join(lines).lower()
        return any(p.search(text) for p in self.DETECT_PATTERNS)

    def parse(self, lines: list[str]) -> OCRResult:
        result = OCRResult(emisor="amex", raw_lines=lines)
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

        confs = [
            result.monto.confidence if result.monto else 0,
            result.fecha.confidence if result.fecha else 0,
        ]
        result.overall_confidence = sum(confs) / len(confs) if confs else 0.0
        return result
