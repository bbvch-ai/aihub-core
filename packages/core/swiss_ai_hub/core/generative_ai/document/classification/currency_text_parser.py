import re
import unicodedata
from typing import ClassVar


class CurrencyTextParser:
    """Reads the ISO 4217 code of a currency written as a code, a symbol or a Swiss abbreviation.

    A bare `$` stays unknown: it is the sign of more than twenty currencies, so reading it as USD would be a guess.
    """

    ALIASES: ClassVar[dict[str, str]] = {
        **dict.fromkeys(["CHF", "FR", "SFR", "FRANKEN", "FRANCS", "FRANCHI"], "CHF"),
        **dict.fromkeys(["EUR", "EURO", "EUROS"], "EUR"),
        **dict.fromkeys(["USD", "US$"], "USD"),
        "GBP": "GBP",
    }
    SYMBOLS: ClassVar[dict[str, str]] = {"€": "EUR", "£": "GBP", "US$": "USD"}
    CODES: ClassVar[frozenset[str]] = frozenset(
        {"CHF", "EUR", "USD", "GBP", "JPY", "CAD", "AUD", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "CNY", "INR"}
    )

    @classmethod
    def parse(cls, raw: str | None) -> str | None:
        if not raw:
            return None
        text = unicodedata.normalize("NFKC", raw).upper()
        for symbol, code in cls.SYMBOLS.items():
            if symbol in text:
                return code
        for token in re.findall(r"[A-Z]+", text):
            if token in cls.ALIASES:
                return cls.ALIASES[token]
            if token in cls.CODES:
                return token
        return None
