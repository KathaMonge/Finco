import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


def format_currency(value: Decimal, currency: str = "ARS") -> str:
    """Formats a Decimal as currency string."""
    if currency == "ARS":
        return f"${value:,.2f}".replace(",", ".")
    return f"{currency} {value:,.2f}"


def parse_date(value: str) -> Optional[date]:
    """Try to parse a date string in common formats."""
    patterns = [
        r"(\d{2})[/-](\d{2})[/-](\d{4})",
        r"(\d{4})[/-](\d{2})[/-](\d{2})",
        r"(\d{2})[/-](\d{2})[/-](\d{2})",
    ]
    for pattern in patterns:
        match = re.match(pattern, value.strip())
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
