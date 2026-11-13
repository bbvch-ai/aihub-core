import calendar
import re
import unicodedata
from collections.abc import Callable
from datetime import date
from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate

type _Builder = Callable[[re.Match[str]], NormalizedDate | None]


class DateTextParser:
    """Reads one date, month, quarter or year written in German, French, Italian or English.

    Never guesses: a slash date whose day and month could be swapped (03/04/2025) and a date that does not exist come
    back as None, and the copied text is kept for a later parser. Dots and dashes are read day first, as everywhere in
    Switzerland and the EU; a slash date is read whichever way only one order allows.
    """

    MONTHS: ClassVar[dict[str, int]] = {
        **dict.fromkeys(["januar", "jänner", "janvier", "janv", "gennaio", "genn", "january", "jan"], 1),
        **dict.fromkeys(["februar", "février", "fevrier", "févr", "fevr", "febbraio", "febbr", "february", "feb"], 2),
        **dict.fromkeys(["märz", "maerz", "mär", "mrz", "mars", "marzo", "march", "mar"], 3),
        **dict.fromkeys(["april", "avril", "avr", "aprile", "apr"], 4),
        **dict.fromkeys(["mai", "maggio", "magg", "may"], 5),
        **dict.fromkeys(["juni", "juin", "giugno", "giu", "june", "jun"], 6),
        **dict.fromkeys(["juli", "juillet", "juil", "luglio", "lug", "july", "jul"], 7),
        **dict.fromkeys(["august", "août", "aout", "agosto", "ago", "aug"], 8),
        **dict.fromkeys(["september", "septembre", "settembre", "sett", "sept", "sep"], 9),
        **dict.fromkeys(["oktober", "okt", "octobre", "ottobre", "ott", "october", "oct"], 10),
        **dict.fromkeys(["november", "novembre", "nov"], 11),
        **dict.fromkeys(["dezember", "dez", "décembre", "decembre", "déc", "dicembre", "dic", "december", "dec"], 12),
    }
    MONTH_PATTERN: ClassVar[str] = "|".join(sorted(MONTHS, key=len, reverse=True))
    ITALIAN_QUARTERS: ClassVar[dict[str, int]] = {"primo": 1, "secondo": 2, "terzo": 3, "quarto": 4}

    ISO_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
    NUMERIC_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b(\d{1,2})\s?([./-])\s?(\d{1,2})\s?\2\s?(\d{4}|\d{2})\b")
    DAY_MONTH_NAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b(\d{{1,2}})\.?[\s-]*({MONTH_PATTERN})\.?[\s,-]*(\d{{4}}|\d{{2}})\b"
    )
    MONTH_NAME_DAY_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b({MONTH_PATTERN})\.?\s+(\d{{1,2}}),?\s+(\d{{4}})\b"
    )
    _MONTH_NAME_YEAR: ClassVar[re.Pattern[str]] = re.compile(rf"\b({MONTH_PATTERN})\.?\s*(\d{{4}})\b")
    _NUMERIC_MONTH_YEAR: ClassVar[re.Pattern[str]] = re.compile(r"^(\d{1,2})\s?[./]\s?(\d{4})$")
    _QUARTER: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:q|t)([1-4])\s*[/-]?\s*(\d{4})\b"
        r"|\b([1-4])\s*(?:\.|er|e|ème|°)?\s*(?:quartal|trimestre)\s*(\d{4})\b"
        r"|\b(primo|secondo|terzo|quarto)\s+trimestre\s*(\d{4})\b"
    )
    _YEAR: ClassVar[re.Pattern[str]] = re.compile(r"^(\d{4})$")

    @classmethod
    def parse(cls, raw: str | None) -> NormalizedDate | None:
        """The first date the text states, at the precision it states it; None when there is none or it is ambiguous."""
        if not raw:
            return None
        text = cls.normalized(raw)
        for pattern, builder in cls._builders():
            match = pattern.search(text)
            if match:
                return builder(match)
        return None

    @classmethod
    def normalized(cls, raw: str) -> str:
        """Lower case, ordinals ("1er", "1st") reduced to their number, and every dash read as a hyphen."""
        text = unicodedata.normalize("NFKC", raw).lower()
        text = re.sub(r"[‐-―−]", "-", text)
        text = re.sub(r"\b(\d{1,2})(?:er|re|st|nd|rd|th|º)\b", r"\1", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def full_year(cls, year: str) -> int:
        number = int(year)
        if len(year) == 4:
            return number
        return 2000 + number if number < 70 else 1900 + number

    @classmethod
    def day(cls, year: int, month: int, day: int) -> NormalizedDate | None:
        try:
            single = date(year, month, day)
        except ValueError:
            return None
        return NormalizedDate(start=single, end=single, precision=DatePrecision.DAY)

    @classmethod
    def month(cls, year: int, month: int) -> NormalizedDate | None:
        if not 1 <= month <= 12:
            return None
        last = calendar.monthrange(year, month)[1]
        return NormalizedDate(start=date(year, month, 1), end=date(year, month, last), precision=DatePrecision.MONTH)

    @classmethod
    def quarter(cls, year: int, quarter: int) -> NormalizedDate:
        first_month = 3 * quarter - 2
        last = calendar.monthrange(year, first_month + 2)[1]
        return NormalizedDate(
            start=date(year, first_month, 1), end=date(year, first_month + 2, last), precision=DatePrecision.QUARTER
        )

    @classmethod
    def _builders(cls) -> list[tuple[re.Pattern[str], _Builder]]:
        return [
            (cls.ISO_PATTERN, lambda m: cls.day(int(m[1]), int(m[2]), int(m[3]))),
            (cls.NUMERIC_PATTERN, cls._numeric_day),
            (cls.DAY_MONTH_NAME_PATTERN, lambda m: cls.day(cls.full_year(m[3]), cls.MONTHS[m[2]], int(m[1]))),
            (cls.MONTH_NAME_DAY_PATTERN, lambda m: cls.day(int(m[3]), cls.MONTHS[m[1]], int(m[2]))),
            (cls._QUARTER, cls._quarter_of),
            (cls._MONTH_NAME_YEAR, lambda m: cls.month(int(m[2]), cls.MONTHS[m[1]])),
            (cls._NUMERIC_MONTH_YEAR, lambda m: cls.month(int(m[2]), int(m[1]))),
            (cls._YEAR, lambda m: cls._year_of(int(m[1]))),
        ]

    @classmethod
    def _numeric_day(cls, match: re.Match[str]) -> NormalizedDate | None:
        first, separator, second, year = int(match[1]), match[2], int(match[3]), cls.full_year(match[4])
        if separator != "/" or first > 12:
            return cls.day(year, second, first)
        if second > 12 or first == second:
            return cls.day(year, first, second)
        return None

    @classmethod
    def _quarter_of(cls, match: re.Match[str]) -> NormalizedDate:
        if match[1]:
            return cls.quarter(int(match[2]), int(match[1]))
        if match[3]:
            return cls.quarter(int(match[4]), int(match[3]))
        return cls.quarter(int(match[6]), cls.ITALIAN_QUARTERS[match[5]])

    @classmethod
    def _year_of(cls, year: int) -> NormalizedDate:
        return NormalizedDate(start=date(year, 1, 1), end=date(year, 12, 31), precision=DatePrecision.YEAR)
