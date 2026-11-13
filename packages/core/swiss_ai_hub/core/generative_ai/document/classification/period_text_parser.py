import re
from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.date_text_parser import DateTextParser
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate

_P = DateTextParser
_TO = r"\s*(?:-|bis|au|al|to)\s*"
_YEAR = r"(\d{4}|\d{2})"


class PeriodTextParser:
    """Reads a period: a range of two dates, a range whose first date leaves out what the second states
    ("1.–28.2.2025", "du 1er au 28 février 2025"), or one date, month, quarter or year standing for the whole period.
    """

    _DAY_MONTH_TO_DATE: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b(\d{{1,2}})\.(\d{{1,2}})\.?{_TO}(\d{{1,2}})\.(\d{{1,2}})\.{_YEAR}\b"
    )
    _DAY_TO_DATE: ClassVar[re.Pattern[str]] = re.compile(rf"\b(\d{{1,2}})\.?{_TO}(\d{{1,2}})\.(\d{{1,2}})\.{_YEAR}\b")
    _DAY_TO_NAMED_DATE: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b(\d{{1,2}})\.?{_TO}(\d{{1,2}})\.?\s*({_P.MONTH_PATTERN})\.?\s*{_YEAR}\b"
    )
    _FULL_DATES: ClassVar[tuple[re.Pattern[str], ...]] = (
        _P.ISO_PATTERN,
        _P.NUMERIC_PATTERN,
        _P.DAY_MONTH_NAME_PATTERN,
        _P.MONTH_NAME_DAY_PATTERN,
    )

    @classmethod
    def parse(cls, raw: str | None) -> NormalizedDate | None:
        if not raw:
            return None
        text = DateTextParser.normalized(raw)
        dates = cls._full_dates(text)
        if len(dates) >= 2:
            return cls._range(dates[0], dates[-1])
        return cls._shortened_range(text) or DateTextParser.parse(raw)

    @classmethod
    def _full_dates(cls, text: str) -> list[NormalizedDate]:
        """Every complete date in the text, in the order written; a reversed pair is then no period at all."""
        found = sorted(
            (match.start(), DateTextParser.parse(match[0]))
            for pattern in cls._FULL_DATES
            for match in pattern.finditer(text)
        )
        return [parsed for _, parsed in found if parsed is not None]

    @classmethod
    def _shortened_range(cls, text: str) -> NormalizedDate | None:
        if match := cls._DAY_MONTH_TO_DATE.search(text):
            year = DateTextParser.full_year(match[5])
            return cls._days(year, int(match[2]), int(match[1]), year, int(match[4]), int(match[3]))
        if match := cls._DAY_TO_DATE.search(text):
            year, month = DateTextParser.full_year(match[4]), int(match[3])
            return cls._days(year, month, int(match[1]), year, month, int(match[2]))
        if match := cls._DAY_TO_NAMED_DATE.search(text):
            year, month = DateTextParser.full_year(match[4]), DateTextParser.MONTHS[match[3]]
            return cls._days(year, month, int(match[1]), year, month, int(match[2]))
        return None

    @classmethod
    def _days(
        cls, start_year: int, start_month: int, start_day: int, end_year: int, end_month: int, end_day: int
    ) -> NormalizedDate | None:
        start = DateTextParser.day(start_year, start_month, start_day)
        end = DateTextParser.day(end_year, end_month, end_day)
        if start is None or end is None:
            return None
        return cls._range(start, end)

    @classmethod
    def _range(cls, first: NormalizedDate, last: NormalizedDate) -> NormalizedDate | None:
        if first.start > last.end:
            return None
        return NormalizedDate(start=first.start, end=last.end, precision=DatePrecision.DAY)
