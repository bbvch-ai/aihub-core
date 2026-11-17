import re
import unicodedata
from typing import ClassVar


class CurrencyTextParser:
    """Reads the ISO 4217 code of a currency written as a code, a symbol or a Swiss abbreviation.

    The currency written first wins, whether code or symbol, so a total followed by its conversion ("CHF 1'250.00
    (€ 1'150.00)") keeps the currency it is stated in. A bare `$` stays unknown: it is the sign of more than twenty
    currencies, so reading it as USD would be a guess.
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
        found = [(text.find(symbol), code) for symbol, code in cls.SYMBOLS.items() if symbol in text]
        found += [
            (match.start(), cls.ALIASES.get(match[0], match[0]))
            for match in re.finditer(r"[A-Z]+", text)
            if match[0] in cls.ALIASES or match[0] in cls.CODES
        ]
        return min(found)[1] if found else None
