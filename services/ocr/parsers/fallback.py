import re
from datetime import date

from services.ocr.models import ExtractedField, ExtractedTransaction, OCRResult
from services.ocr.parsers.base import BaseParser
from utils.helpers import parse_amount, parse_date


_DATE_RE = r"(?:\d{1,2})?[\s.\-_/=\u2013]*?[A-Za-z\d]{3,5}[\s.\-_/=\u2013]*?\d{1,4}"

LINE_TX_PATTERN = re.compile(
    r"(\d{6,})\s+"
    + r"(" + _DATE_RE + r")"
    + r"\s+(.+?)"
    + r"\s+[R:?I\s]+"
    + r"(?:\s+\S+)?\s*$",
    re.IGNORECASE,
)

LINE_TX_GENERIC = re.compile(
    r"(" + _DATE_RE + r")"
    + r"\s+"
    + r"(.+?)"
    + r"\s+"
    + r"(\S+)\s*$",
    re.IGNORECASE,
)


class FallbackParser(BaseParser):
    AMOUNT_PATTERNS = [
        re.compile(r"(?:total|t[o0]tal|tot[a]?l?|importe|monto|amount)\s*:?\s*\$?\s*([\d.,]+)", re.IGNORECASE),
        re.compile(r"(?:per[ií]odo|del\s+\d|al\s+\d).*?\s(\d{4,})\s*$"),
        re.compile(r"\$?\s*([\d.,]+)\s*(?:ars|usd)?", re.IGNORECASE),
        re.compile(r"\b(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))\b"),
    ]

    DATE_PATTERNS = [
        re.compile(r"(\d{2}[/-]\d{2}[/-]\d{4})"),
        re.compile(r"(\d{4}[/-]\d{2}[/-]\d{2})"),
        re.compile(r"(\d{1,2}[\s.\-_/=\u2013]*?[A-Za-z]{3,4}[\s.\-_/=\u2013]*?\d{2,4})"),
    ]

    CARD_PATTERNS = [
        re.compile(r"(?:tarjeta|card|nro)\s*:?\s*[\*x]?(\d{4})", re.IGNORECASE),
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    ]

    def detect(self, lines: list[str]) -> bool:
        return True

    _FOOTER_KEYWORDS = re.compile(
        r"total|subtotal|saldo|per[ií]odo|del\s+\d|al\s+\d",
        re.IGNORECASE,
    )

    def _extract_transactions(self, lines: list[str]) -> list[ExtractedTransaction]:
        txs: list[ExtractedTransaction] = []
        seen = set()
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            if self._FOOTER_KEYWORDS.search(line):
                continue

            match = LINE_TX_PATTERN.search(line)
            if match:
                raw_date = match.group(2)
                desc = match.group(3).strip()
                last_token = match.group(0).split()[-1] if match.group(0).split() else ""
                parsed_d = parse_date(raw_date)
                parsed_a = parse_amount(last_token)
                if parsed_a and parsed_d and parsed_a > 0:
                    key = (str(parsed_d), str(parsed_a))
                    if key not in seen:
                        seen.add(key)
                        txs.append(ExtractedTransaction(
                            amount=parsed_a,
                            date=parsed_d,
                            description=desc,
                            confidence=0.65,
                            raw_text=line,
                        ))
                continue

            match = LINE_TX_GENERIC.search(line)
            if match:
                raw_date = match.group(1)
                desc = match.group(2).strip()
                last_token = match.group(3)
                parsed_d = parse_date(raw_date)
                parsed_a = parse_amount(last_token)
                if parsed_a and parsed_d and parsed_a > 0:
                    key = (str(parsed_d), str(parsed_a))
                    if key not in seen:
                        seen.add(key)
                        txs.append(ExtractedTransaction(
                            amount=parsed_a,
                            date=parsed_d,
                            description=desc,
                            confidence=0.55,
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
                if amount and amount > 0:
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
