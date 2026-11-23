import unicodedata
from collections.abc import Iterator
from datetime import date

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_parser import PathDateParser

pytestmark = pytest.mark.unit

TODAY = date(2026, 11, 20)

_YEAR_2026 = (date(2026, 1, 1), date(2026, 12, 31), DatePrecision.YEAR)
_YEAR_2025 = (date(2025, 1, 1), date(2025, 12, 31), DatePrecision.YEAR)
_MARCH_2026 = (date(2026, 3, 1), date(2026, 3, 31), DatePrecision.MONTH)
_APRIL_6 = (date(2026, 4, 6), date(2026, 4, 6), DatePrecision.DAY)
_MARCH_15_2025 = (date(2025, 3, 15), date(2025, 3, 15), DatePrecision.DAY)
_Q1_2026 = (date(2026, 1, 1), date(2026, 3, 31), DatePrecision.QUARTER)


@pytest.fixture(autouse=True)
def _fresh_cache() -> Iterator[None]:
    PathDateParser._parsed.cache_clear()
    yield
    PathDateParser._parsed.cache_clear()


def _read(path: str) -> tuple[date, date, DatePrecision] | None:
    parsed = PathDateParser.parse(path, TODAY)
    return (parsed.start, parsed.end, parsed.precision) if parsed else None


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("invoices/2026/a.pdf", _YEAR_2026),
        ("invoices_2025/a.pdf", _YEAR_2025),
        ("marketing/2026/x.pdf", _YEAR_2026),
        ("projects/data set 2025.pdf", _YEAR_2025),
        ("1990/x.pdf", (date(1990, 1, 1), date(1990, 12, 31), DatePrecision.YEAR)),
        ("2026/12.pdf", _YEAR_2026),
        ("2026/14/x.pdf", _YEAR_2026),
        ("2026/Dezember.pdf", _YEAR_2026),
        ("x/06/04/2026.pdf", _YEAR_2026),
        ("Mai_Nguyen_2025.pdf", _YEAR_2025),
    ],
)
def test_a_year_folder_or_name_dates_the_whole_year(path: str, expected: tuple[date, date, DatePrecision]) -> None:
    assert _read(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        "2026/03/a.pdf",
        "2026/march/x.pdf",
        "2026/März/x.pdf",
        "2026/maerz/x.pdf",
        "2026/mars/x.pdf",
        "2026/marzo/x.pdf",
        "2026/03 März/x.pdf",
        "2026/03_mar/x.pdf",
        "reports/2026-03/a.pdf",
        "reports/2026_03/a.pdf",
        "reports/03.2026/a.pdf",
        "reports/202603/a.pdf",
        "März 2026/x.pdf",
        "Rechnungen Mär 2026.pdf",
        "MÄR 2026.pdf",
        unicodedata.normalize("NFD", "März 2026.pdf"),
        "2026\\03\\f.pdf",
    ],
)
def test_a_month_in_folders_or_names_dates_the_month(path: str) -> None:
    assert _read(path) == _MARCH_2026


@pytest.mark.parametrize(
    ("path", "year", "month"),
    [
        ("2026/févr/x.pdf", 2026, 2),
        ("2026/gen/x.pdf", 2026, 1),
        ("reports/12-2025/a.pdf", 2025, 12),
        ("reports/201812/a.pdf", 2018, 12),
        ("2026 juin/x.pdf", 2026, 6),
        ("luglio-2026.pdf", 2026, 7),
        ("mag 2026.pdf", 2026, 5),
    ],
)
def test_months_in_every_language_and_form(path: str, year: int, month: int) -> None:
    parsed = _read(path)

    assert parsed is not None
    assert (parsed[0].year, parsed[0].month, parsed[2]) == (year, month, DatePrecision.MONTH)


@pytest.mark.parametrize(
    "path",
    [
        "scans/2026-04-06_scan.pdf",
        "scans/2026_04_06.pdf",
        "scans/2026.04.06.pdf",
        "scans/20260406.pdf",
        "IMG_20260406_1234.jpg",
        "x/06.04.2026.pdf",
        "x/6.4.2026.pdf",
        "x/06.04.26.pdf",
        "x/6. April 2026.pdf",
        "x/06-04-2026.pdf",
        "x/06_04_2026.pdf",
    ],
)
def test_a_date_in_a_file_name_dates_the_day(path: str) -> None:
    assert _read(path) == _APRIL_6


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("x/13.04.2026.pdf", date(2026, 4, 13)),
        ("x/15 mars 2026.pdf", date(2026, 3, 15)),
        ("x/15_März_2026.pdf", date(2026, 3, 15)),
        ("x/2026/03/14/f.pdf", date(2026, 3, 14)),
        ("x/2026-03/14/f.pdf", date(2026, 3, 14)),
        ("2026/march/2026-03-14.pdf", date(2026, 3, 14)),
        ("Q2_2026/20260415.pdf", date(2026, 4, 15)),
    ],
)
def test_days_in_names_and_nested_folders(path: str, expected: date) -> None:
    assert _read(path) == (expected, expected, DatePrecision.DAY)


@pytest.mark.parametrize("path", ["Scan_2025-03-15_001.pdf", "2025-03-15-0001.pdf", "15.03.2025_1.pdf"])
def test_a_counter_after_a_date_keeps_the_date(path: str) -> None:
    assert _read(path) == _MARCH_15_2025


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("x/04-06-2026.pdf", date(2026, 6, 4)),
        ("x/13-04-2026.pdf", date(2026, 4, 13)),
        ("x/06_06_2026.pdf", date(2026, 6, 6)),
    ],
)
def test_numeric_dates_are_always_read_day_first(path: str, expected: date) -> None:
    assert _read(path) == (expected, expected, DatePrecision.DAY)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("Q1 2026/x.pdf", _Q1_2026),
        ("2026-Q1/x.pdf", _Q1_2026),
        ("1. Quartal 2026/x.pdf", _Q1_2026),
        ("T1 2026/x.pdf", _Q1_2026),
        ("1er trimestre 2026/x.pdf", _Q1_2026),
        ("primo trimestre 2026/x.pdf", _Q1_2026),
        ("2026_Q2/x.pdf", (date(2026, 4, 1), date(2026, 6, 30), DatePrecision.QUARTER)),
        ("2026/2. Quartal/f.pdf", (date(2026, 4, 1), date(2026, 6, 30), DatePrecision.QUARTER)),
        ("q3-2026.pdf", (date(2026, 7, 1), date(2026, 9, 30), DatePrecision.QUARTER)),
        ("2026/Q3/f.pdf", (date(2026, 7, 1), date(2026, 9, 30), DatePrecision.QUARTER)),
        ("2026/T4/f.pdf", (date(2026, 10, 1), date(2026, 12, 31), DatePrecision.QUARTER)),
        ("invoices/2024/q1/a.pdf", (date(2024, 1, 1), date(2024, 3, 31), DatePrecision.QUARTER)),
    ],
)
def test_quarters_in_folders_and_names(path: str, expected: tuple[date, date, DatePrecision]) -> None:
    assert _read(path) == expected


@pytest.mark.parametrize(
    ("path", "start", "end"),
    [
        ("Jan-März 2025/x.pdf", date(2025, 1, 1), date(2025, 3, 31)),
        ("x/01.01.–31.03.2025.pdf", date(2025, 1, 1), date(2025, 3, 31)),
        ("Kontoauszug_01.01.2025-31.03.2025.pdf", date(2025, 1, 1), date(2025, 3, 31)),
        ("Januar bis März 2025.pdf", date(2025, 1, 1), date(2025, 3, 31)),
        ("x/1.-15.3.2025.pdf", date(2025, 3, 1), date(2025, 3, 15)),
        ("Rechnung Mai - Juni 2025.pdf", date(2025, 5, 1), date(2025, 6, 30)),
        ("x/06.04.2026 - 06.05.2026.pdf", date(2026, 4, 6), date(2026, 5, 6)),
        ("x/6.4.26 - 10.4.26.pdf", date(2026, 4, 6), date(2026, 4, 10)),
        ("x/1-15 März 2025.pdf", date(2025, 3, 1), date(2025, 3, 15)),
        ("x/1 bis 15 März 2025.pdf", date(2025, 3, 1), date(2025, 3, 15)),
        ("x/du 1 au 15 mars 2025.pdf", date(2025, 3, 1), date(2025, 3, 15)),
        ("x/15-20 Mai 2025.pdf", date(2025, 5, 15), date(2025, 5, 20)),
    ],
)
def test_a_range_in_one_segment_is_read_as_its_full_span(path: str, start: date, end: date) -> None:
    parsed = _read(path)

    assert parsed is not None
    assert (parsed[0], parsed[1]) == (start, end)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("Liegenschaften/2000 Neuchâtel/a.pdf", (date(2000, 1, 1), date(2000, 12, 31), DatePrecision.YEAR)),
        ("Rechnung_2025_03.pdf", (date(2025, 3, 1), date(2025, 3, 31), DatePrecision.MONTH)),
        ("20261201.pdf", (date(2026, 12, 1), date(2026, 12, 1), DatePrecision.DAY)),
        ("10.11.12.pdf", (date(2012, 11, 10), date(2012, 11, 10), DatePrecision.DAY)),
        ("2025/1/x.pdf", (date(2025, 1, 1), date(2025, 1, 31), DatePrecision.MONTH)),
        ("2025/August/x.pdf", (date(2025, 8, 1), date(2025, 8, 31), DatePrecision.MONTH)),
    ],
)
def test_accepted_false_readings_are_pinned(path: str, expected: tuple[date, date, DatePrecision]) -> None:
    assert _read(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        "contracts/acme.pdf",
        "march/x.pdf",
        "generic/mar.txt",
        "T1_test.pdf",
        "q1/x.pdf",
    ],
)
def test_a_path_without_a_date_has_none(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    "path",
    [
        "Rechnung_20261234.pdf",
        "20260230.pdf",
        "04.13.2026.pdf",
        "x/04-13-2026.pdf",
        "x/04_13_2026.pdf",
        "2026-13-01.pdf",
        "31.02.2026.pdf",
    ],
)
def test_an_invalid_date_gives_none_and_is_never_swapped(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    "path",
    [
        "v2.1.pdf",
        "release-2026.1.3.zip",
        "release-2026.10.3.zip",
        "Rechnung_Nr_2026-0415.pdf",
        "Seite 3 von 12.pdf",
        "ID 3999.pdf",
        "1234567890.pdf",
    ],
)
def test_versions_and_numbers_are_no_dates(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    "path", ["1985/x.pdf", "Liegenschaften/1950 Sion/a.pdf", "2028/x.pdf", "12026/x.pdf", "20266/x.pdf"]
)
def test_a_year_outside_the_window_or_glued_to_digits_is_no_date(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize("path", ["FY2025/x.pdf", "2025-2026/x.pdf"])
def test_a_span_of_years_is_unknown(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize("path", ["06-04-26.pdf", "06_04_26.pdf", "6.4.26.pdf", "2026/03/06-04-26.pdf"])
def test_an_ambiguous_two_digit_year_makes_the_path_unknown(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    "path", ["2025/20260406.pdf", "2026/march/20260406.pdf", "Q1-Q2 2025/x.pdf", "2025/Q1-Q2 2025/x.pdf"]
)
def test_dates_that_do_not_nest_make_the_path_unknown(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    "path",
    [
        "Rechnungen_Jan_Feb_2025.pdf",
        "Q1_Q2_2025/x.pdf",
        "Jan+Feb 2025.pdf",
        "Januar und Februar 2025.pdf",
        "Jan, Feb, März 2025.pdf",
        "x/1. und 15.03.2025.pdf",
    ],
)
def test_listed_months_or_days_no_span_covers_make_the_path_unknown(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    "path", ["Rechnung März 2025 - 2. Mahnung.pdf", "März_2025_Mai_Nguyen.pdf", "x/2025-03-15.2.pdf"]
)
def test_a_month_word_or_suffix_next_to_a_date_is_a_safe_loss(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    "path",
    [
        "SIA_2024_Merkblatt.pdf",
        "Rechnung Nr. 1985.pdf",
        "RE-2025-03.pdf",
        "Rechnung_Nr_12_2026.pdf",
        "201812.pdf",
        "Version 10.11.12.pdf",
    ],
)
def test_a_number_behind_an_identifier_is_no_date(path: str) -> None:
    assert _read(path) is None


def test_the_year_window_follows_today() -> None:
    assert PathDateParser.parse("2028/x.pdf", date(2027, 1, 1)) is not None
    assert PathDateParser.parse("2028/x.pdf", date(2026, 12, 31)) is None


def test_a_parsed_path_is_memoised_and_each_call_returns_a_new_date() -> None:
    first = PathDateParser.parse("invoices/2026/03/a.pdf", TODAY)
    hits = PathDateParser._parsed.cache_info().hits

    second = PathDateParser.parse("invoices/2026/03/a.pdf", TODAY)

    assert PathDateParser._parsed.cache_info().hits == hits + 1
    assert first == second
    assert first is not second


@pytest.mark.parametrize(
    "path",
    [
        "x/1_15_März_2025.pdf",
        "x/1+15 März 2025.pdf",
        "x/1, 15 März 2025.pdf",
        "x/1 und 15 März 2025.pdf",
        "x/Rapport 2025-03-01 - 15.pdf",
    ],
)
def test_a_bare_day_number_next_to_a_date_is_never_read_as_one_end(path: str) -> None:
    """Without the span check, "1 und 15 März 2025" read as 15 March and a period of 1-14 March left it out."""
    assert _read(path) is None


@pytest.mark.parametrize(
    "path",
    [
        "Verträge ab 2020/x.pdf",
        "seit 2020/x.pdf",
        "since 2020/x.pdf",
        "dès 2021/x.pdf",
        "dal 2021/x.pdf",
        "2020-heute/x.pdf",
        "2020_bis_heute/x.pdf",
        "2020-present/x.pdf",
        "2020 ff/x.pdf",
        "pre-2020/x.pdf",
        "Archiv bis 2019/x.pdf",
        "vor 2010/x.pdf",
        "Rechnungen 2024 und älter/x.pdf",
        "ab März 2025/x.pdf",
        "seit 01.03.2025/x.pdf",
        "von 01.03.2025 bis heute/x.pdf",
        "à partir de 2021/x.pdf",
        "jusqu'à 2020/x.pdf",
        "2020 und später/x.pdf",
        "2020 und neuer/x.pdf",
        "2020 onwards/x.pdf",
        "2020 or later/x.pdf",
        "2020 and later/x.pdf",
        "2020 e successivi/x.pdf",
        "2020 et suivants/x.pdf",
        "2020 et après/x.pdf",
        "2020+/x.pdf",
        "2020-/x.pdf",
        "-2019/x.pdf",
        ">2020/x.pdf",
        "<2020/x.pdf",
        "2020 to date/x.pdf",
        "2020 à ce jour/x.pdf",
        "2020 ad oggi/x.pdf",
        "ab Mitte 2020/x.pdf",
        "bis Ende 2019/x.pdf",
        "jusqu'à fin 2019/x.pdf",
        "à partir de mi-2020/x.pdf",
        "up to 2019/x.pdf",
        "through 2019/x.pdf",
    ],
)
def test_a_date_with_an_open_bound_makes_the_path_unknown(path: str) -> None:
    assert _read(path) is None


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("Abrechnung 2025/x.pdf", _YEAR_2025),
        ("Vorlage 2025.pdf", _YEAR_2025),
        ("Absender/2025/x.pdf", _YEAR_2025),
        ("Update 2025/x.pdf", _YEAR_2025),
        ("Datenbank 2025/x.pdf", _YEAR_2025),
        ("Plus Konto 2025/x.pdf", _YEAR_2025),
        ("Mitarbeiter 2025/x.pdf", _YEAR_2025),
        ("Midland 2025/x.pdf", _YEAR_2025),
        ("Up 2025/x.pdf", _YEAR_2025),
        ("Later 2025/x.pdf", _YEAR_2025),
        ("Mitte 2025/x.pdf", _YEAR_2025),
        ("x/2025-03.pdf", (date(2025, 3, 1), date(2025, 3, 31), DatePrecision.MONTH)),
        ("x/2025-03-15.pdf", _MARCH_15_2025),
        ("Januar bis März 2025.pdf", (date(2025, 1, 1), date(2025, 3, 31), DatePrecision.MONTH)),
    ],
)
def test_open_bound_words_never_match_inside_other_words_or_a_written_range(
    path: str, expected: tuple[date, date, DatePrecision]
) -> None:
    assert _read(path) == expected


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("03 März 2026/x.pdf", _MARCH_2026),
        ("x/03_März_2026.pdf", _MARCH_2026),
        ("x/01 Januar 2026.pdf", (date(2026, 1, 1), date(2026, 1, 31), DatePrecision.MONTH)),
        ("x/12 Dezember 2025.pdf", (date(2025, 12, 1), date(2025, 12, 31), DatePrecision.MONTH)),
        ("x/15 März 2026.pdf", (date(2026, 3, 15), date(2026, 3, 15), DatePrecision.DAY)),
        ("x/3. März 2026.pdf", (date(2026, 3, 3), date(2026, 3, 3), DatePrecision.DAY)),
    ],
)
def test_a_two_digit_number_equal_to_its_month_reads_the_whole_month(
    path: str, expected: tuple[date, date, DatePrecision]
) -> None:
    assert _read(path) == expected


@pytest.mark.parametrize("path", ["15-mar-2025.pdf", "15 März 2025.pdf", "15._März_2025.pdf"])
def test_a_day_joined_to_its_month_by_a_dash_or_a_space_is_still_a_day(path: str) -> None:
    assert _read(path) == _MARCH_15_2025


def test_a_spaced_dash_does_not_join_a_number_to_the_month_after_it() -> None:
    """Read as 3 March, "Kapitel 3 - März 2025" was left out of a period of 10 to 20 March; the number is now a bare
    number next to the month, which no span covers."""
    assert _read("x/Kapitel 3 - März 2025.pdf") is None


def _folders(*folders: str) -> list[tuple[date, date] | None]:
    return [(dated.start, dated.end) if dated else None for dated in PathDateParser.folder_dates(list(folders), TODAY)]


_Q1_2025 = (date(2025, 1, 1), date(2025, 3, 31))
_MARCH_2025 = (date(2025, 3, 1), date(2025, 3, 31))
_ALL_2025 = (date(2025, 1, 1), date(2025, 12, 31))


@pytest.mark.parametrize(
    ("folders", "expected"),
    [
        (("invoices", "2025", "**"), [None, _ALL_2025, None]),
        (("invoices", "2025", "q1"), [None, _ALL_2025, _Q1_2025]),
        (("2025", "03"), [_ALL_2025, _MARCH_2025]),
        (("2025-03",), [_MARCH_2025]),
        (("202503", "x"), [_MARCH_2025, None]),
        (("März 2025",), [_MARCH_2025]),
        (("2025_Q1",), [_Q1_2025]),
    ],
)
def test_a_folder_that_is_only_a_date_gives_its_date_also_under_its_dated_parent(
    folders: tuple[str, ...], expected: list[tuple[date, date] | None]
) -> None:
    assert _folders(*folders) == expected


@pytest.mark.parametrize(
    "folders",
    [("invoices-2025",), ("Nr 2025",), ("2025.pdf",), ("2028",), ("invoices", "q1"), ("Rechnungen", "03")],
)
def test_a_folder_that_names_more_than_a_date_or_none_certain_gives_none(folders: tuple[str, ...]) -> None:
    assert _folders(*folders) == [None] * len(folders)


def test_a_quarter_under_a_folder_that_also_names_something_is_still_read_under_its_year() -> None:
    """The parent names more than a date, so it is no date folder itself, yet it dates its quarter as `parse` does."""
    assert _folders("invoices-2025", "q1") == [None, _Q1_2025]
