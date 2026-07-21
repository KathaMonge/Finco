"""Tests for OCR parsers (without actual OCR engine)."""

from services.ocr.parsers.visa import VisaParser
from services.ocr.parsers.mastercard import MastercardParser
from services.ocr.parsers.amex import AmexParser
from services.ocr.parsers.fallback import FallbackParser
from services.ocr.parsers.registry import ParserRegistry


SAMPLE_VISA_TEXT = [
    "VISA CREDITO",
    "Titular: JUAN PEREZ",
    "FECHA: 15/01/2024",
    "COMERCIO: Supermercado Central",
    "TOTAL: $ 1,250.50",
    "TARJETA: **** 1234",
]

SAMPLE_MASTERCARD_TEXT = [
    "MASTERCARD GOLD",
    "FECHA: 2024/03/20",
    "TOTAL: 850.00",
    "GRACIAS POR SU COMPRA",
]

SAMPLE_AMEX_TEXT = [
    "AMERICAN EXPRESS",
    "Date: 10/05/2024",
    "Amount: 3200.00 ARS",
]

UNKNOWN_TEXT = [
    "TIENDA DE ROPA",
    "15/06/2024",
    "TOTAL: $ 450.00",
    "NRO: 9876",
]


class TestVisaParser:
    def test_detect(self):
        parser = VisaParser()
        assert parser.detect(SAMPLE_VISA_TEXT) is True
        assert parser.detect(UNKNOWN_TEXT) is False

    def test_parse(self):
        parser = VisaParser()
        result = parser.parse(SAMPLE_VISA_TEXT)
        assert result.emisor == "visa"
        assert result.monto is not None
        assert result.fecha is not None
        assert result.comercio is not None
        assert result.tarjeta is not None
        assert float(result.monto.value) == 1250.50


class TestMastercardParser:
    def test_detect(self):
        parser = MastercardParser()
        assert parser.detect(SAMPLE_MASTERCARD_TEXT) is True

    def test_parse(self):
        parser = MastercardParser()
        result = parser.parse(SAMPLE_MASTERCARD_TEXT)
        assert result.emisor == "mastercard"
        assert result.monto is not None


class TestAmexParser:
    def test_detect(self):
        parser = AmexParser()
        assert parser.detect(SAMPLE_AMEX_TEXT) is True

    def test_parse(self):
        parser = AmexParser()
        result = parser.parse(SAMPLE_AMEX_TEXT)
        assert result.emisor == "amex"
        assert result.monto is not None


class TestFallbackParser:
    def test_detect_always_true(self):
        parser = FallbackParser()
        assert parser.detect([]) is True
        assert parser.detect(UNKNOWN_TEXT) is True

    def test_parse_unknown(self):
        parser = FallbackParser()
        result = parser.parse(UNKNOWN_TEXT)
        assert result.emisor == "fallback"
        assert result.monto is not None
        assert result.monto.confidence < 0.9


class TestParserRegistry:
    def test_detect_visa(self):
        emisor = ParserRegistry.detect_emisor(SAMPLE_VISA_TEXT)
        assert emisor == "visa"

    def test_detect_mastercard(self):
        emisor = ParserRegistry.detect_emisor(SAMPLE_MASTERCARD_TEXT)
        assert emisor == "mastercard"

    def test_detect_amex(self):
        emisor = ParserRegistry.detect_emisor(SAMPLE_AMEX_TEXT)
        assert emisor == "amex"

    def test_detect_fallback(self):
        emisor = ParserRegistry.detect_emisor(UNKNOWN_TEXT)
        assert emisor == "fallback"
