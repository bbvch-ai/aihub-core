import re
import unicodedata
from typing import ClassVar


class TaxIdTextParser:
    """Reads a Swiss UID or an EU/UK VAT number into one form: country prefix and digits, no separators or suffix.

    `CHE-123.456.788 MWST` becomes `CHE123456788`, as Swico's QR-bill syntax writes it minus the prefix. A Swiss UID
    must pass its check digit, since a misread digit would otherwise be stored as another company's number. EU numbers
    are checked against their country's format only. A German tax office number (Steuernummer) has no standard form and
    stays unread.
    """

    SWISS_WEIGHTS: ClassVar[tuple[int, ...]] = (5, 4, 3, 2, 7, 6, 5, 4)
    VAT_FORMATS: ClassVar[dict[str, str]] = {
        "AT": r"U\d{8}",
        "BE": r"[01]\d{9}",
        "BG": r"\d{9,10}",
        "CY": r"\d{8}[A-Z]",
        "CZ": r"\d{8,10}",
        "DE": r"\d{9}",
        "DK": r"\d{8}",
        "EE": r"\d{9}",
        "EL": r"\d{9}",
        "ES": r"[A-Z0-9]\d{7}[A-Z0-9]",
        "FI": r"\d{8}",
        "FR": r"[A-HJ-NP-Z0-9]{2}\d{9}",
        "GB": r"\d{12}|\d{9}",
        "HR": r"\d{11}",
        "HU": r"\d{8}",
        "IE": r"\d{7}[A-W][A-I]?",
        "IT": r"\d{11}",
        "LT": r"\d{12}|\d{9}",
        "LU": r"\d{8}",
        "LV": r"\d{11}",
        "MT": r"\d{8}",
        "NL": r"\d{9}B\d{2}",
        "PL": r"\d{10}",
        "PT": r"\d{9}",
        "RO": r"\d{2,10}",
        "SE": r"\d{12}",
        "SI": r"\d{8}",
        "SK": r"\d{10}",
    }
    # A lookahead, so candidates overlap: "MWST-Nr. CHE-…" must not swallow the UID into a candidate for "MW".
    _CANDIDATE: ClassVar[re.Pattern[str]] = re.compile(r"\b(?=(CHE|[A-Z]{2})[\s:.-]*((?:[0-9A-Z][\s.-]?){6,16}))")

    @classmethod
    def parse(cls, raw: str | None) -> str | None:
        if not raw:
            return None
        text = unicodedata.normalize("NFKC", raw).upper()
        for match in cls._CANDIDATE.finditer(text):
            country, body = match[1], re.sub(r"[\s.-]", "", match[2])
            if country == "CHE":
                return cls._swiss(body)
            if country in cls.VAT_FORMATS and (vat := re.match(rf"(?:{cls.VAT_FORMATS[country]})(?![0-9])", body)):
                return f"{country}{vat[0]}"
        return None

    @classmethod
    def _swiss(cls, body: str) -> str | None:
        """The UID if its ninth digit is the modulus-11 check digit of the first eight, else None."""
        if not re.match(r"\d{9}(?!\d)", body):
            return None
        digits = [int(digit) for digit in body[:9]]
        check = 11 - sum(weight * digit for weight, digit in zip(cls.SWISS_WEIGHTS, digits, strict=False)) % 11
        check = 0 if check == 11 else check
        if check == 10 or check != digits[8]:
            return None
        return f"CHE{body[:9]}"
