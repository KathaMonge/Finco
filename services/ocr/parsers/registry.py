from services.ocr.parsers.base import BaseParser
from services.ocr.parsers.fallback import FallbackParser


class ParserRegistry:
    _parsers: dict[str, type[BaseParser]] = {}

    @classmethod
    def register(cls, emisor: str):
        def wrapper(parser_cls: type[BaseParser]):
            cls._parsers[emisor] = parser_cls
            return parser_cls
        return wrapper

    @classmethod
    def get_parser(cls, emisor: str) -> BaseParser:
        parser_cls = cls._parsers.get(emisor)
        if parser_cls:
            return parser_cls()
        return FallbackParser()

    @classmethod
    def detect_emisor(cls, lines: list[str]) -> str:
        for emisor, parser_cls in cls._parsers.items():
            if parser_cls().detect(lines):
                return emisor
        return "fallback"
