import re
from datetime import date

from services.ocr.models import ExtractedField, ExtractedTransaction, OCRResult
from services.ocr.parsers.base import BaseParser
from utils.helpers import parse_amount, parse_date


LINE_TX_PATTERN = re.compile(
    r"(\d{2}[/-]\d{2}[/-]\d{2,4})"   # date
    r"\s+(.+?)"                        # description (non-greedy)
    r"\s+\$?\s*([\d.,]+)\s*$",        # amount at end of line
    re.IGNORECASE,
)


class FallbackParser(BaseParser):
    AMOUNT_PATTERNS = [
        re.compile(r"(?:total|importe|monto|amount)\s*:?\s*\$?\s*([\d.,]+)", re.IGNORECASE),
        re.compile(r"\$?\s*([\d.,]+)\s*(?:ars|usd)?", re.IGNORECASE),
        re.compile(r"\b(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))\b"),
    ]

    DATE_PATTERNS = [
        re.compile(r"(\d{2}[/-]\d{2}[/-]\d{4})"),
        re.compile(r"(\d{4}[/-]\d{2}[/-]\d{2})"),
    ]

    CARD_PATTERNS = [
        re.compile(r"(?:tarjeta|card|nro)\s*:?\s*[\*x]?(\d{4})", re.IGNORECASE),
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    ]

    def detect(self, lines: list[str]) -> bool:
        return True

    def _extract_transactions(self, lines: list[str]) -> list[ExtractedTransaction]:
        txs: list[ExtractedTransaction] = []
        for line in lines:
            line = line.strip()
            match = LINE_TX_PATTERN.search(line)
            if match:
                raw_date = match.group(1)
                desc = match.group(2).strip()
                raw_amount = match.group(3)
                parsed_d = parse_date(raw_date)
                parsed_a = parse_amount(raw_amount)
                if parsed_a and parsed_d:
                    txs.append(ExtractedTransaction(
                        amount=parsed_a,
                        date=parsed_d,
                        description=desc,
                        confidence=0.6,
                        raw_text=line,
                    ))
        return txs

    def parse(self, lines: list[str]) -> OCRResult:
        result = OCRResult(emisor="fallback", raw_lines=lines)
        full_text = " ".join(lines)

        for pattern in self.AMOUNT_PATTERNS:
            match = pattern.search(full_text)
            if match:
                amount = parse_amount(match.group(1))
                if amount:
                    result.monto = ExtractedField(
                        value=str(amount),
                        confidence=0.7,
                        raw_text=match.group(0),
                        method="fuzzy_regex",
                    )
                    break

        for pattern in self.DATE_PATTERNS:
            match = pattern.search(full_text)
            if match:
                parsed = parse_date(match.group(1))
                if parsed:
                    result.fecha = ExtractedField(
                        value=parsed.isoformat(),
                        confidence=0.6,
                        raw_text=match.group(0),
                        method="fuzzy_regex",
                    )
                    break

        for pattern in self.CARD_PATTERNS:
            match = pattern.search(full_text)
            if match:
                card_str = match.group(0).replace(" ", "").replace("-", "")
                if len(card_str) >= 4:
                    result.tarjeta = ExtractedField(
                        value=card_str[-4:],
                        confidence=0.5,
                        raw_text=match.group(0),
                        method="fuzzy_regex",
                    )
                    break

        result.transactions = self._extract_transactions(lines)

        confs = [
            result.monto.confidence if result.monto else 0,
            result.fecha.confidence if result.fecha else 0,
        ]
        result.overall_confidence = sum(confs) / len(confs) if confs else 0.0
        return result
