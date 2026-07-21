import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


MONTH_ABBRS = {
    "jan": 1, "ene": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8, "aug": 8, "sep": 9,
    "oct": 10, "nov": 11, "dic": 12, "dec": 12,
}

_MONTH_OCR_GARBLES = {
    "j": {"j", "i", "l", "1"},
    "a": {"a"},
    "n": {"n", "h", "m", "ri"},
    "u": {"u"},
    "f": {"f"},
    "e": {"e"},
    "b": {"b"},
    "m": {"m"},
    "r": {"r"},
    "p": {"p"},
    "s": {"s", "5"},
    "o": {"o", "0"},
    "c": {"c"},
    "t": {"t"},
    "d": {"d"},
    "l": {"l", "i", "1", "|"},
    "i": {"i", "l", "1", "|"},
    "g": {"g", "9"},
}


_DIGIT_TO_LETTER = str.maketrans("0123456789", "oizasgtrbn")

_KNOWN_MONTH_GARBLES = {
    "iun": 6, "jiun": 6, "ilun": 6, "iiun": 6, "i11n": 6,
    "i1un": 6, "i1in": 6, "nun": 6, "jln": 6, "jiin": 6,
    "juiun": 6, "jiu": 6, "i1n": 6,
    "jlul": 7, "juln": 7, "julu": 7,
    "jau": 1, "janu": 1, "jani": 1,
    "febr": 2, "febe": 2,
    "marz": 3, "mari": 3,
    "abri": 4, "abrii": 4,
    "mayy": 5, "nay": 5,
    "agost": 8, "agoo": 8,
    "sept": 9, "sepe": 9,
    "octu": 10, "octo": 10,
    "novi": 11, "novv": 11,
    "diet": 12, "diee": 12, "dicc": 12,
}


def _fuzzy_match_month(token: str) -> Optional[int]:
    """Match a month abbreviation even with OCR garbling.

    Handles cases like JIUN->JUN, IlUN->JUN, I11N->JUN, etc.
    Uses sliding window to find the closest 3-char match.
    """
    clean = token.lower().strip()
    cleaned = re.sub(r"[^a-z]", "", clean)

    if clean in _KNOWN_MONTH_GARBLES:
        return _KNOWN_MONTH_GARBLES[clean]
    if cleaned in _KNOWN_MONTH_GARBLES:
        return _KNOWN_MONTH_GARBLES[cleaned]

    if cleaned in MONTH_ABBRS:
        return MONTH_ABBRS[cleaned]

    normalized = clean.translate(_DIGIT_TO_LETTER)
    norm_cleaned = re.sub(r"[^a-z]", "", normalized)
    if norm_cleaned in _KNOWN_MONTH_GARBLES:
        return _KNOWN_MONTH_GARBLES[norm_cleaned]
    if norm_cleaned in MONTH_ABBRS:
        return MONTH_ABBRS[norm_cleaned]

    for text in (cleaned, norm_cleaned):
        if len(text) < 3:
            continue
        best_month = None
        best_dist = 3
        for abbr, month_num in MONTH_ABBRS.items():
            if len(abbr) != 3:
                continue
            for start in range(len(text) - 2):
                window = text[start:start + 3]
                dist = sum(1 for a, b in zip(window, abbr) if a != b)
                if dist < best_dist:
                    best_dist = dist
                    best_month = month_num
        if best_month and best_dist <= 1:
            return best_month

    for text in (cleaned, norm_cleaned):
        if len(text) < 3:
            continue
        best_month = None
        best_dist = 3
        for abbr, month_num in MONTH_ABBRS.items():
            if len(abbr) != 3:
                continue
            for start in range(len(text) - 2):
                window = text[start:start + 3]
                dist = sum(1 for a, b in zip(window, abbr) if a != b)
                if dist < best_dist:
                    best_dist = dist
                    best_month = month_num
        if best_month and best_dist <= 2:
            return best_month

    return None


def format_currency(value: Decimal, currency: str = "ARS") -> str:
    """Formats a Decimal as currency string."""
    if currency == "ARS":
        return f"${value:,.2f}".replace(",", ".")
    return f"{currency} {value:,.2f}"


def parse_date(value: str) -> Optional[date]:
    """Try to parse a date string in common formats.

    Handles OCR-garbled dates like:
    - 2-MAY-2 -> 2026-05-02 (truncated year)
    - 3.JUN-26 -> 2026-06-03 (dot separator)
    - 5=IlUN-2 -> 2026-06-05 (garbled separators and month)
    - –IUN-2 -> 2026-06-? (missing day, garbled month)
    - 15/03/2024 -> 2024-03-15 (standard)
    """
    cleaned = value.strip()

    match = re.match(
        r"(\d{1,2})?[\s.\-_/=\u2013]*?([A-Za-z\d]{3,5})[\s.\-_/=\u2013]*?(\d{1,4})",
        cleaned,
    )
    if match:
        day_str, month_str, year_str = match.groups()
        month_num = _fuzzy_match_month(month_str)
        if month_num:
            day = int(re.sub(r"[^\d]", "", day_str)) if day_str else 1
            year_digits = re.sub(r"[^\d]", "", year_str)
            if len(year_digits) == 1:
                from datetime import datetime as _dt
                cur = _dt.now().year
                d = int(year_digits)
                cand_tens = 2000 + d * 10 + (cur % 10)
                cand_ones = 2000 + (cur // 10 % 10) * 10 + d
                year = cand_tens if abs(cur - cand_tens) <= abs(cur - cand_ones) else cand_ones
            elif len(year_digits) == 2:
                year = 2000 + int(year_digits)
            else:
                year = int(year_digits)
            try:
                return date(year, month_num, day)
            except ValueError:
                pass

    patterns = [
        r"(\d{2})[/-](\d{2})[/-](\d{4})",
        r"(\d{4})[/-](\d{2})[/-](\d{2})",
        r"(\d{2})[/-](\d{2})[/-](\d{2})",
    ]
    for pattern in patterns:
        match = re.match(pattern, cleaned)
        if match:
            groups = match.groups()
            if len(groups[2]) == 4:
                year, month, day = int(groups[2]), int(groups[1]), int(groups[0])
            elif len(groups[0]) == 4:
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            else:
                day, month, year = int(groups[0]), int(groups[1]), 2000 + int(groups[2])
            try:
                return date(year, month, day)
            except ValueError:
                continue
    return None


def parse_amount(value: str) -> Optional[Decimal]:
    """Extract a Decimal amount from a string."""
    cleaned = re.sub(r"[^\d,.]", "", value)
    if cleaned.count(",") == 1 and not cleaned.count("."):
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(",") == 1 and cleaned.count(".") >= 1:
        cleaned = cleaned.replace(",", "")
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
