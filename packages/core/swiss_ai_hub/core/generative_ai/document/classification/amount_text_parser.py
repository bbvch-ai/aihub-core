import re
import unicodedata
from typing import ClassVar


class AmountTextParser:
    """Reads an amount written with any of the separators used in Switzerland, the EU and English-speaking countries.

    `12'496.36`, `12’496.36`, `12.496,36`, `12 496,36` and `12,496.36` are all 12496.36; the Swiss `1'250.–` is
    1250.00. A minus before or after the number, or brackets around it, make it negative. With one separator, three
    digits after it mean thousands, as no currency is written with three decimals.
    """

    _ZERO_CENTS: ClassVar[re.Pattern[str]] = re.compile(r"([.,])\s?-{1,2}(?!\d)")
    _NUMBER: ClassVar[re.Pattern[str]] = re.compile(r"\d(?:[\d'’  .,]*\d)?")
    _NEGATIVE_BEFORE: ClassVar[re.Pattern[str]] = re.compile(r"[-(]\s*(?:[a-z.]{1,4}\s*)?$", re.IGNORECASE)
    _NEGATIVE_AFTER: ClassVar[re.Pattern[str]] = re.compile(r"^\s*[-)]")

    @classmethod
    def parse(cls, raw: str | None) -> float | None:
        if not raw:
            return None
        text = re.sub(r"[‐-―−]", "-", unicodedata.normalize("NFKC", raw))
        text = cls._ZERO_CENTS.sub(r"\g<1>00", text)
        match = cls._NUMBER.search(text)
        if match is None:
            return None
        value = cls._value(re.sub(r"['’  ]", "", match[0]))
        if value is None:
            return None
        negative = cls._NEGATIVE_BEFORE.search(text[: match.start()]) or cls._NEGATIVE_AFTER.search(text[match.end() :])
        return round(-value if negative else value, 2)

    @classmethod
    def _value(cls, number: str) -> float | None:
        last_dot, last_comma = number.rfind("."), number.rfind(",")
        if last_dot >= 0 and last_comma >= 0:
            decimal = "." if last_dot > last_comma else ","
        elif last_dot >= 0 or last_comma >= 0:
            separator = "." if last_dot >= 0 else ","
            decimal = None if cls._is_thousands(number, separator) else separator
        else:
            decimal = None
        integer_part, _, fraction = number.rpartition(decimal) if decimal else (number, "", "")
        digits = re.sub(r"[.,]", "", integer_part)
        if not digits.isdigit() or (fraction and not fraction.isdigit()):
            return None
        return float(f"{digits}.{fraction}" if fraction else digits)

    @classmethod
    def _is_thousands(cls, number: str, separator: str) -> bool:
        groups = number.split(separator)
        return len(groups) > 2 or len(groups[-1]) == 3
