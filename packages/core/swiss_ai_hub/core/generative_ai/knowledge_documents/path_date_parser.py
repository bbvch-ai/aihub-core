import re
from collections.abc import Callable
from datetime import date
from functools import lru_cache
from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.date_text_parser import DateTextParser
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.document.classification.period_text_parser import PeriodTextParser

type _Builder = Callable[[re.Match[str]], NormalizedDate | None]
type _Parsed = tuple[date, date, DatePrecision]

_B = r"(?<![^\W_])"
_E = r"(?![^\W_])"
_G = r"(?<!\d[._-])"
_H = r"(?![._-]\d)"
_WORD_JOINER = r"(?<![^\W_])(?:bis|au|à|al|a|to|until|through|und|and|et|e)(?![^\W_])"
_JOINER = rf"[ _]*(?:[-_+&,]|{_WORD_JOINER})[ _]*"
_CONSUMED = "\x00"
_LEFTOVER = "\x01"
_QUARTER_WORDS = r"(?:quartal|quarter|trimestre)"
_BARE_DAY = r"(?<![^\W_])\d{1,2}(?![^\W_])"
_OPEN_BEFORE = (
    r"(?<![^\W_])(?:up[ _-]+to|ab|seit|since|after|dès|depuis|à partir|dal|dalla|dai|dagli|a partire|dopo|nach|bis|"
    r"vor|before|until|till|through|thru|pre|prior|avant|après|apres|jusqu|fino|entro|prima)(?![^\W_])"
)
"""Words before a date that make it one end of an open period: "ab 2020", "up to 2019", "pre-2020"."""
_OPEN_AFTER = (
    r"(?<![^\W_])(?:to[ _-]+date|[àa][ _-]+ce[ _-]+jour|ad[ _-]+oggi|bis|after|before|avant|après|apres|prima|dopo|"
    r"älter|aelter|older|earlier|früher|frueher|precedenti|antérieurs|antérieures|anterieurs|später|spaeter|neuer|"
    r"newer|later|onwards?|successivi|seguenti|suivants|ultérieurs|ulterieurs|postérieurs|posterieurs|heute|today|"
    r"present|aujourd|oggi|ff|laufend|ongoing)(?![^\W_])"
)
"""Words after a date that make it one end of an open period: "2020-heute", "2024 und älter", "2020 onwards"."""
_OPEN_FILLER = (
    r"(?:[ _.:'-]+(?:de|du|d|del|dem|der|den|the|à|au|a|al|il|le|la|ende|mitte|anfang|end|mid|early|late|fin|début|"
    r"debut|mi|fine|inizio|metà|meta)(?![^\W_])){0,2}"
)
_OPEN_EDGE = r"[-+<>≤≥]"
_AND = r"(?:(?:und|and|et|e|oder|or|ou|o)[ _-]+)?"


class PathDateParser:
    """Reads the date a document's path gives it: year and month folders, dates in file names, quarters, and a range
    written in one folder or file name.

    Never narrows on doubt. A period then leaves out every document dated outside it, so a path whose date might not
    contain the document's true date reads as no date and the document is kept: ambiguous two-digit years, listed
    months, quarters or days no span covers, a date that is one end of an open period ("ab 2020", "2020-heute"), a
    year glued to letters ("rev2025", "2025er"), and dates of different segments that do not nest. Numbers behind an
    identifier ("Nr", "SIA", "v") and years outside `EARLIEST_YEAR` to next year give no date. The one decided
    exception: numeric dates with a four-digit year are read day first, as in Switzerland and the EU, and one that does
    not exist that way gives no date rather than a swapped one.
    """

    EARLIEST_YEAR: ClassVar[int] = 1990
    PARSED_PATHS_CACHED: ClassVar[int] = 50_000
    MONTHS: ClassVar[dict[str, int]] = {**DateTextParser.MONTHS, "gen": 1, "mag": 5}
    MONTH_PATTERN: ClassVar[str] = "|".join(sorted(MONTHS, key=len, reverse=True))

    _SEPARATORS: ClassVar[re.Pattern[str]] = re.compile(r"[/\\]+")
    _EXTENSION: ClassVar[re.Pattern[str]] = re.compile(r"\.(?=\d{0,4}[a-z])[a-z0-9]{1,5}$", re.IGNORECASE)
    _TWO_DIGIT_YEAR_AMBIGUOUS: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}(\d{{1,2}})([-_])(\d{{1,2}})\2(\d{{2}}){_E}"
    )
    _ID_PREFIX: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}(?:nr|no|n°|nº|num|#|sia|iso|din|sn|plz|id|ref|re|rg|inv|art|pos|version|vers|v)[ ._:#-]*$"
    )
    _GLUED_YEAR: ClassVar[re.Pattern[str]] = re.compile(r"(?<=[^\W\d_])\d{4}(?!\d)|(?<!\d)\d{4}(?=[^\W\d_])")

    _DAY_YEAR_FIRST: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}{_G}(\d{{4}})([-_.])(\d{{2}})\2(\d{{2}})(?!\.\d){_E}"
    )
    _DAY_COMPACT: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}(\d{{4}})(\d{{2}})(\d{{2}}){_E}")
    _DAY_FIRST: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}{_G}(\d{{1,2}})([-_.])(\d{{1,2}})\2(\d{{4}})(?!\.\d){_E}")
    _DAY_SHORT_YEAR: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}(?<!\d\.)(\d{{2}})\.(\d{{2}})\.(\d{{2}})(?!\.\d){_E}"
    )
    _DAY_MONTH_NAME: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}(\d{{1,2}})\.?(?:[ _]*|-)({MONTH_PATTERN})\.?[ _-]*(\d{{4}}){_E}"
    )
    _QUARTER_YEAR: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}[qt]([1-4])[ _-]?(\d{{4}}){_E}")
    _YEAR_QUARTER: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}(\d{{4}})[ _-]?[qt]([1-4]){_E}")
    _QUARTER_WORD_YEAR: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}([1-4])(?:\.|er|e|ème|°)?[ _-]?{_QUARTER_WORDS}[ _-]?(\d{{4}}){_E}"
    )
    _ITALIAN_QUARTER_YEAR: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}(primo|secondo|terzo|quarto)[ _-]trimestre[ _-]?(\d{{4}}){_E}"
    )
    _MONTH_NAME_YEAR: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}({MONTH_PATTERN})\.?[ _-]*(\d{{4}}){_E}")
    _YEAR_MONTH_NAME: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}(\d{{4}})[ _-]*({MONTH_PATTERN}){_E}")
    _YEAR_MONTH: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}{_G}(\d{{4}})([-_.])(\d{{2}}){_H}{_E}")
    _MONTH_YEAR: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}{_G}(\d{{2}})([-_.])(\d{{4}}){_H}{_E}")
    _FOLDER_MONTH: ClassVar[re.Pattern[str]] = re.compile(r"^(\d{4})(\d{2})$")
    _YEAR: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}{_G}(\d{{4}}){_H}{_E}")

    _LEFTOVER_TOKEN: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_B}(?:(?:{MONTH_PATTERN}|[qt][1-4]|{_QUARTER_WORDS}){_E}|\d{{1,2}}\.\d{{1,2}}\.\d{{2}}{_E}"
        rf"|\d{{1,2}}\.(?:\d{{1,2}}\.?)?|(\d{{4}}){_E})"
    )
    _RANGE_SUSPECT: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_LEFTOVER}{_JOINER}[{_CONSUMED}{_LEFTOVER}]|[{_CONSUMED}{_LEFTOVER}]{_JOINER}{_LEFTOVER}"
    )
    _LISTED: ClassVar[re.Pattern[str]] = re.compile(rf"{_B}(?:{MONTH_PATTERN}|[qt][1-4]|{_QUARTER_WORDS}){_E}")
    _BARE_DAY_BY_DATE: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_BARE_DAY}{_JOINER}{_CONSUMED}|{_CONSUMED}(?: *[+&,] *| +- *| *- +|[ _]+{_WORD_JOINER}[ _]+){_BARE_DAY}"
    )
    """A day number written before a date, or after it with a connector or a spaced dash, as in "1-15 März 2025" or
    "2025-03-01 - 15"; a counter glued on with "_" or "-" ("_1", "-0001") is not one."""
    _OPEN_BOUND: ClassVar[re.Pattern[str]] = re.compile(
        rf"{_OPEN_BEFORE}{_OPEN_FILLER}[ _.:'-]*{_CONSUMED}|{_CONSUMED}[ _-]*{_AND}{_OPEN_AFTER}"
        rf"|^[ _]*{_OPEN_EDGE}[ _]*{_CONSUMED}|{_CONSUMED}[ _]*{_OPEN_EDGE}[ _]*$"
    )
    """A word next to a date that makes it one end of an open period ("ab Mitte 2020", "2020-heute", "2024 und älter"),
    or a sign between it and the segment's edge ("2020+", "-2019", ">2020")."""

    _NAME_LEFT: ClassVar[re.Pattern[str]] = re.compile(r"[^\W_]")
    _NUMBER_ALONE: ClassVar[re.Pattern[str]] = re.compile(r"^(\d{1,2})$")
    _MONTH_ALONE: ClassVar[re.Pattern[str]] = re.compile(rf"^(?:(\d{{1,2}})[ ._-]*)?({MONTH_PATTERN})\.?$")
    _QUARTER_ALONE: ClassVar[re.Pattern[str]] = re.compile(
        rf"^(?:[qt]([1-4])|([1-4])(?:\.|er|e|ème|°)?[ _-]?{_QUARTER_WORDS}|(primo|secondo|terzo|quarto)[ _-]trimestre)$"
    )

    @classmethod
    def parse(cls, path: str, today: date | None = None) -> NormalizedDate | None:
        """The period the path dates its document in, or None when it gives no date or no certain one."""
        parsed = cls._parsed(path, (today or date.today()).year + 1)
        if parsed is None:
            return None
        start, end, precision = parsed
        return NormalizedDate(start=start, end=end, precision=precision)

    @classmethod
    def folder_dates(cls, folders: list[str], today: date | None = None) -> list[NormalizedDate | None]:
        """The date each folder is, read as `parse` reads folders: a year, month or quarter folder, also one under its
        dated parent ("2025/q1"). None for a folder that also names something else ("invoices-2025") or gives no
        certain date, so a caller that replaces date folders never drops a name."""
        years = range(cls.EARLIEST_YEAR, (today or date.today()).year + 2)
        dates: list[NormalizedDate | None] = []
        parent: NormalizedDate | None = None
        for folder in folders:
            parent, only_a_date = cls._folder_date(DateTextParser.normalized(folder), years, parent)
            dates.append(parent if only_a_date else None)
        return dates

    @classmethod
    def _folder_date(
        cls, folder: str, years: range, parent: NormalizedDate | None
    ) -> tuple[NormalizedDate | None, bool]:
        """The date a folder gives, on its own or under its dated parent, and whether the folder is nothing but it."""
        dates = cls._segment_dates(folder, years, is_folder=True)
        if dates == []:
            inherited = cls._from_parent(folder, parent)
            return inherited, inherited is not None
        if dates is None or len(dates) != 1:
            return None, False
        working, _ = cls._own_dates(folder, cls._builders(years, is_folder=True))
        return dates[0], cls._NAME_LEFT.search(working) is None

    @staticmethod
    @lru_cache(maxsize=PARSED_PATHS_CACHED)
    def _parsed(path: str, latest_year: int) -> _Parsed | None:
        """Memoised as a small tuple: a selection, the planner and the listing tool read the same paths again."""
        years = range(PathDateParser.EARLIEST_YEAR, latest_year + 1)
        innermost = PathDateParser._innermost(PathDateParser._candidates(PathDateParser._segments(path), years))
        return (innermost.start, innermost.end, innermost.precision) if innermost else None

    @classmethod
    def _segments(cls, path: str) -> list[str]:
        parts = [part for part in cls._SEPARATORS.split(path) if part]
        if parts:
            parts[-1] = cls._EXTENSION.sub("", parts[-1])
        return [DateTextParser.normalized(part) for part in parts]

    @classmethod
    def _candidates(cls, segments: list[str], years: range) -> list[NormalizedDate]:
        """Every date the segments give, in path order; a single ambiguous segment makes the whole path undated."""
        candidates: list[NormalizedDate] = []
        parent: NormalizedDate | None = None
        for index, segment in enumerate(segments):
            is_folder = index < len(segments) - 1
            dates = cls._segment_dates(segment, years, is_folder)
            if dates is None:
                return []
            if not dates and is_folder and (inherited := cls._from_parent(segment, parent)):
                dates = [inherited]
            candidates.extend(dates)
            parent = dates[0] if len(dates) == 1 else None
        return candidates

    @classmethod
    def _segment_dates(cls, segment: str, years: range, is_folder: bool) -> list[NormalizedDate] | None:
        """The segment's own dates, its span when it writes a range or a list, or None when it is ambiguous."""
        if cls._TWO_DIGIT_YEAR_AMBIGUOUS.search(segment):
            return None
        working, dates = cls._own_dates(segment, cls._builders(years, is_folder))
        if cls._has_glued_year(working, years):
            return None
        if not cls._is_span_candidate(working, dates, years):
            return None if dates and cls._OPEN_BOUND.search(working) else dates
        span = PeriodTextParser.parse(segment.replace("_", " "))
        return [span] if span is not None and cls._spans_all(span, dates, years) else None

    @classmethod
    def _own_dates(
        cls, segment: str, builders: list[tuple[re.Pattern[str], _Builder]]
    ) -> tuple[str, list[NormalizedDate]]:
        """Each pattern in turn; what it matched is blanked, so a later, coarser pattern never reads it again."""
        working, dates = segment, []
        for pattern, builder in builders:
            spans = []
            for match in pattern.finditer(working):
                spans.append(match.span())
                if not cls._ID_PREFIX.search(working[: match.start()]) and (found := builder(match)):
                    dates.append(found)
            working = cls._blanked(working, spans, _CONSUMED)
        return working, dates

    @classmethod
    def _builders(cls, years: range, is_folder: bool) -> list[tuple[re.Pattern[str], _Builder]]:
        folder_months: list[tuple[re.Pattern[str], _Builder]] = [
            (cls._FOLDER_MONTH, lambda m: cls._month(years, int(m[1]), int(m[2])))
        ]
        return [
            (cls._DAY_YEAR_FIRST, lambda m: cls._day(years, int(m[1]), int(m[3]), int(m[4]))),
            (cls._DAY_COMPACT, lambda m: cls._day(years, int(m[1]), int(m[2]), int(m[3]))),
            (cls._DAY_FIRST, lambda m: cls._day(years, int(m[4]), int(m[3]), int(m[1]))),
            (cls._DAY_SHORT_YEAR, lambda m: cls._day(years, DateTextParser.full_year(m[3]), int(m[2]), int(m[1]))),
            (cls._DAY_MONTH_NAME, lambda m: cls._day_or_month(years, m)),
            (cls._QUARTER_YEAR, lambda m: cls._quarter(years, int(m[2]), int(m[1]))),
            (cls._YEAR_QUARTER, lambda m: cls._quarter(years, int(m[1]), int(m[2]))),
            (cls._QUARTER_WORD_YEAR, lambda m: cls._quarter(years, int(m[2]), int(m[1]))),
            (
                cls._ITALIAN_QUARTER_YEAR,
                lambda m: cls._quarter(years, int(m[2]), DateTextParser.ITALIAN_QUARTERS[m[1]]),
            ),
            (cls._MONTH_NAME_YEAR, lambda m: cls._month(years, int(m[2]), cls.MONTHS[m[1]])),
            (cls._YEAR_MONTH_NAME, lambda m: cls._month(years, int(m[1]), cls.MONTHS[m[2]])),
            (cls._YEAR_MONTH, lambda m: cls._month(years, int(m[1]), int(m[3]))),
            (cls._MONTH_YEAR, lambda m: cls._month(years, int(m[3]), int(m[1]))),
            *(folder_months if is_folder else []),
            (cls._YEAR, lambda m: cls._year_of_token(years, int(m[1]))),
        ]

    @classmethod
    def _has_glued_year(cls, working: str, years: range) -> bool:
        """No pattern reads a year glued to letters, yet "rev2025" or "2025er" may be the document's year, so its
        segment is unknown. One glued to an identifier ("RE2025-003") stays a number, as "Nr 2025" does."""
        return any(
            int(match[0]) in years and not cls._ID_PREFIX.search(working[: match.start()])
            for match in cls._GLUED_YEAR.finditer(working)
        )

    @classmethod
    def _is_span_candidate(cls, working: str, dates: list[NormalizedDate], years: range) -> bool:
        """Whether the segment may write a range or a list, which its own dates would read as one end or one item."""
        if cls._RANGE_SUSPECT.search(cls._marked(working, years)):
            return True
        if dates and cls._innermost(dates) is None:
            return True
        finer_than_year = any(found.precision is not DatePrecision.YEAR for found in dates)
        return finer_than_year and bool(cls._LISTED.search(working) or cls._BARE_DAY_BY_DATE.search(working))

    @classmethod
    def _marked(cls, working: str, years: range) -> str:
        """The working text with each leftover date token marked; a four-digit number counts only as a year."""
        return cls._LEFTOVER_TOKEN.sub(
            lambda m: m[0] if m[1] and int(m[1]) not in years else _LEFTOVER * len(m[0]), working
        )

    @classmethod
    def _spans_all(cls, span: NormalizedDate, dates: list[NormalizedDate], years: range) -> bool:
        if span.start.year not in years or span.end.year not in years:
            return False
        return all(
            span.start <= found.start and found.end <= span.end and (found.start, found.end) != (span.start, span.end)
            for found in dates
        )

    @classmethod
    def _from_parent(cls, segment: str, parent: NormalizedDate | None) -> NormalizedDate | None:
        """A month, quarter or day folder, read only under a folder dated exactly a year or a month."""
        if parent is None:
            return None
        year, month = parent.start.year, parent.start.month
        if parent == DateTextParser.year(year):
            return cls._under_year(segment, year)
        if parent == DateTextParser.month(year, month) and (match := cls._NUMBER_ALONE.match(segment)):
            return DateTextParser.day(year, month, int(match[1]))
        return None

    @classmethod
    def _under_year(cls, segment: str, year: int) -> NormalizedDate | None:
        if match := cls._NUMBER_ALONE.match(segment):
            return DateTextParser.month(year, int(match[1]))
        if match := cls._MONTH_ALONE.match(segment):
            month = cls.MONTHS[match[2]]
            return DateTextParser.month(year, month) if match[1] is None or int(match[1]) == month else None
        if match := cls._QUARTER_ALONE.match(segment):
            quarter = match[1] or match[2]
            return DateTextParser.quarter(year, int(quarter) if quarter else DateTextParser.ITALIAN_QUARTERS[match[3]])
        return None

    @staticmethod
    def _innermost(dates: list[NormalizedDate]) -> NormalizedDate | None:
        """The shortest date, the deepest on a tie, if all others contain it; dates that do not nest give None."""
        if not dates:
            return None
        innermost = min(reversed(dates), key=lambda found: found.end - found.start)
        if all(found.start <= innermost.start and innermost.end <= found.end for found in dates):
            return innermost
        return None

    @staticmethod
    def _blanked(text: str, spans: list[tuple[int, int]], mark: str) -> str:
        for start, end in spans:
            text = text[:start] + mark * (end - start) + text[end:]
        return text

    @classmethod
    def _day_or_month(cls, years: range, match: re.Match[str]) -> NormalizedDate | None:
        """A two-digit number equal to the month's own ("03 März 2026") may number the month rather than date the day,
        so the whole month is read; "3. März" and "15 März" stay days."""
        month = cls.MONTHS[match[2]]
        if len(match[1]) == 2 and int(match[1]) == month:
            return cls._month(years, int(match[3]), month)
        return cls._day(years, int(match[3]), month, int(match[1]))

    @staticmethod
    def _day(years: range, year: int, month: int, day: int) -> NormalizedDate | None:
        return DateTextParser.day(year, month, day) if year in years else None

    @staticmethod
    def _month(years: range, year: int, month: int) -> NormalizedDate | None:
        return DateTextParser.month(year, month) if year in years else None

    @staticmethod
    def _quarter(years: range, year: int, quarter: int) -> NormalizedDate | None:
        return DateTextParser.quarter(year, quarter) if year in years else None

    @staticmethod
    def _year_of_token(years: range, year: int) -> NormalizedDate | None:
        return DateTextParser.year(year) if year in years else None
