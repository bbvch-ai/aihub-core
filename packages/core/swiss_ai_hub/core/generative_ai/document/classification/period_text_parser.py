import re
from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.date_text_parser import DateTextParser
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.document.classification.slash_date_order import SlashDateOrder

_P = DateTextParser
_TO = r"\s*(?:-|bis|au|à|al|a|to|until|through)\s*"
_YEAR = r"(\d{4}|\d{2})"
_MONTH = rf"({_P.MONTH_PATTERN})\.?"


class PeriodTextParser:
    """Reads a period: a range of two dates, a range whose first date leaves out what the second states
    ("1.–28.2.2025", "1. Januar bis 31. März 2025", "Januar – März 2025"), or one date, month, quarter or year standing
    for the whole period.

    Never guesses: a text that names two dates or months but in no form read here stores no period, rather than the one
    date a single-date reading would find, which is only one end of the range.
    """

    _DAY_MONTH_TO_DATE: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b(\d{{1,2}})\.(\d{{1,2}})\.?{_TO}(\d{{1,2}})\.(\d{{1,2}})\.{_YEAR}\b"
    )
    _DAY_TO_DATE: ClassVar[re.Pattern[str]] = re.compile(rf"\b(\d{{1,2}})\.?{_TO}(\d{{1,2}})\.(\d{{1,2}})\.{_YEAR}\b")
    _DAY_TO_NAMED_DATE: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b(\d{{1,2}})\.?{_TO}(\d{{1,2}})\.?\s*{_MONTH}\s*{_YEAR}\b"
    )
    _NAMED_DAY_TO_NAMED_DATE: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b(\d{{1,2}})\.?\s*{_MONTH}{_TO}(\d{{1,2}})\.?\s*{_MONTH}\s*{_YEAR}\b"
    )
    _MONTH_DAY_TO_MONTH_DAY_YEAR: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b{_MONTH}\s+(\d{{1,2}}){_TO}{_MONTH}\s+(\d{{1,2}}),?\s+(\d{{4}})\b"
    )
    _MONTH_TO_NAMED_MONTH: ClassVar[re.Pattern[str]] = re.compile(rf"\b{_MONTH}{_TO}{_MONTH}\s*(\d{{4}})\b")
    _NAMED_MONTH_TO_NAMED_MONTH: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b{_MONTH}\s*(\d{{4}}){_TO}{_MONTH}\s*(\d{{4}})\b"
    )
    _NUMERIC_MONTH_TO_MONTH: ClassVar[re.Pattern[str]] = re.compile(
        rf"\b(\d{{1,2}})[./](\d{{4}}){_TO}(\d{{1,2}})[./](\d{{4}})\b"
    )
    _FULL_DATE_PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        _P.ISO_PATTERN,
        _P.NUMERIC_PATTERN,
        _P.DAY_MONTH_NAME_PATTERN,
        _P.MONTH_NAME_DAY_PATTERN,
    )
    _MONTH_NAME: ClassVar[re.Pattern[str]] = re.compile(rf"\b(?:{_P.MONTH_PATTERN})\b")
    _START_WORDS: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:ab|seit|beginn\w*|stellenantritt|eintritt\w*|in kraft|dès|à partir|début|prend effet|en vigueur|"
        r"a partire|dal|decorr\w*|inizio|in vigore|from|start\w*|commenc\w*|effective)\b"
    )
    _END_WORDS: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:bis|endet|ende|ablauf|vertragsende|jusqu|fin|échéance|expir\w*|fino|scad\w*|termina|until|till|"
        r"through|ends?)\b"
    )
    _TAKES_EFFECT: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:in kraft|en vigueur|in vigore|takes effect|comes into force)\b"
    )
    _DAY_AND_MONTH_NAME: ClassVar[re.Pattern[str]] = re.compile(
        rf"(?:\b\d{{1,2}}\W{{0,2}}\s*)?\b(?:{_P.MONTH_PATTERN})\b"
    )
    _YEAR: ClassVar[re.Pattern[str]] = re.compile(r"\b\d{4}\b")
    _REACH: ClassVar[int] = 60
    _OPEN_ENDED: ClassVar[re.Pattern[str]] = re.compile(
        r"unbefristet|unbestimmte zeit|auf weiteres|indéterminée|indeterminat|indefinite|until terminated|"
        r"until further notice|until (?:they are|it is) completed"
    )

    @classmethod
    def parse(cls, raw: str | None, slash_order: SlashDateOrder | None = None) -> NormalizedDate | None:
        if not raw:
            return None
        text = DateTextParser.normalized(raw)
        if written_range := cls._written_range(text, slash_order):
            return written_range
        dates = cls._full_dates(text, slash_order)
        if len(dates) + len(cls._MONTH_NAME.findall(cls._without_full_dates(text))) >= 2:
            return None
        return DateTextParser.parse(raw, slash_order)

    @classmethod
    def stated_ends(
        cls, raw: str | None, slash_order: SlashDateOrder | None = None, context: str | None = None
    ) -> tuple[bool, bool]:
        """Whether the text states the period's start and its end.

        A single date is the whole period unless a word next to it says which end it is: "ab 1. April 2025", "tritt am
        1. März 2026 in Kraft" or a term "auf unbestimmte Zeit" state only the start, "bis 31. Dezember 2026" only the
        end. Only the words between the date and its neighbouring numbers count, so "Lieferdatum 14.03.2025, zahlbar
        bis 13.04.2025" stays one day. The copy is read first, then the document line it came from, since a model
        often copies the date without the word.
        """
        if not raw:
            return False, False
        text = DateTextParser.normalized(raw)
        if cls._written_range(text, slash_order):
            return True, True
        if ends := cls._ends_named_around(text, *cls._date_span(text)):
            return ends
        surrounding = DateTextParser.normalized(context) if context else ""
        position = surrounding.find(text)
        if position >= 0 and (ends := cls._ends_named_around(surrounding, position, position + len(text))):
            return ends
        return True, True

    @classmethod
    def _ends_named_around(cls, text: str, date_start: int, date_end: int) -> tuple[bool, bool] | None:
        before = re.split(r"\d", text[max(0, date_start - cls._REACH) : date_start])[-1]
        after = re.split(r"\d", text[date_end : date_end + cls._REACH])[0]
        if cls._OPEN_ENDED.search(f"{before} {after}") or cls._TAKES_EFFECT.search(after):
            return True, False
        nearest = cls._end_words(before)[-1:]
        return (nearest[0], not nearest[0]) if nearest else None

    @classmethod
    def _end_words(cls, text: str) -> list[bool]:
        """For each word naming an end of a period, in the order written, whether it names the start."""
        return [
            starts
            for _, starts in sorted(
                (match.start(), pattern is cls._START_WORDS)
                for pattern in (cls._START_WORDS, cls._END_WORDS)
                for match in pattern.finditer(text)
            )
        ]

    @classmethod
    def _date_span(cls, text: str) -> tuple[int, int]:
        """Where the date stands: its first complete date, else its first month name with any day before it, else its
        first year."""
        for pattern in (*cls._FULL_DATE_PATTERNS, cls._DAY_AND_MONTH_NAME, cls._YEAR):
            if match := min(pattern.finditer(text), key=lambda found: found.start(), default=None):
                return match.start(), match.end()
        return len(text), len(text)

    @classmethod
    def _written_range(cls, text: str, slash_order: SlashDateOrder | None) -> NormalizedDate | None:
        """A range the text writes out, in a shortened form or as two complete dates."""
        if written_range := cls._shortened_range(text) or cls._month_range(text):
            return written_range
        dates = cls._full_dates(text, slash_order)
        return cls._range(dates[0], dates[-1]) if len(dates) >= 2 else None

    @classmethod
    def _full_dates(cls, text: str, slash_order: SlashDateOrder | None) -> list[NormalizedDate]:
        """Every complete date in the text, in the order written; a reversed pair is then no period at all."""
        found = sorted(
            (match.start(), DateTextParser.parse(match[0], slash_order))
            for pattern in cls._FULL_DATE_PATTERNS
            for match in pattern.finditer(text)
        )
        return [parsed for _, parsed in found if parsed is not None]

    @classmethod
    def _without_full_dates(cls, text: str) -> str:
        """The text with every complete date taken out, so a month named inside one is not counted twice."""
        for pattern in cls._FULL_DATE_PATTERNS:
            text = pattern.sub(" ", text)
        return text

    @classmethod
    def _shortened_range(cls, text: str) -> NormalizedDate | None:
        """A range of days whose first date leaves out the month or year the second one states."""
        if match := cls._DAY_MONTH_TO_DATE.search(text):
            year = DateTextParser.full_year(match[5])
            return cls._days(year, int(match[2]), int(match[1]), year, int(match[4]), int(match[3]))
        if match := cls._DAY_TO_DATE.search(text):
            year, month = DateTextParser.full_year(match[4]), int(match[3])
            return cls._days(year, month, int(match[1]), year, month, int(match[2]))
        if match := cls._DAY_TO_NAMED_DATE.search(text):
            year, month = DateTextParser.full_year(match[4]), DateTextParser.MONTHS[match[3]]
            return cls._days(year, month, int(match[1]), year, month, int(match[2]))
        if match := cls._NAMED_DAY_TO_NAMED_DATE.search(text):
            year = DateTextParser.full_year(match[5])
            months = DateTextParser.MONTHS
            return cls._days(year, months[match[2]], int(match[1]), year, months[match[4]], int(match[3]))
        if match := cls._MONTH_DAY_TO_MONTH_DAY_YEAR.search(text):
            year, months = int(match[5]), DateTextParser.MONTHS
            return cls._days(year, months[match[1]], int(match[2]), year, months[match[3]], int(match[4]))
        return None

    @classmethod
    def _month_range(cls, text: str) -> NormalizedDate | None:
        """A range of whole months: "Januar – März 2025", "Dezember 2024 – Februar 2025", "01.2025 – 03.2025"."""
        months = DateTextParser.MONTHS
        if match := cls._NAMED_MONTH_TO_NAMED_MONTH.search(text):
            return cls._months(int(match[2]), months[match[1]], int(match[4]), months[match[3]])
        if match := cls._MONTH_TO_NAMED_MONTH.search(text):
            year = int(match[3])
            return cls._months(year, months[match[1]], year, months[match[2]])
        if match := cls._NUMERIC_MONTH_TO_MONTH.search(text):
            return cls._months(int(match[2]), int(match[1]), int(match[4]), int(match[3]))
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
    def _months(cls, start_year: int, start_month: int, end_year: int, end_month: int) -> NormalizedDate | None:
        start = DateTextParser.month(start_year, start_month)
        end = DateTextParser.month(end_year, end_month)
        if start is None or end is None:
            return None
        return cls._range(start, end, DatePrecision.MONTH)

    @classmethod
    def _range(
        cls, first: NormalizedDate, last: NormalizedDate, precision: DatePrecision = DatePrecision.DAY
    ) -> NormalizedDate | None:
        if first.start > last.end:
            return None
        return NormalizedDate(start=first.start, end=last.end, precision=precision)
