from datetime import date

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.period_text_parser import PeriodTextParser

pytestmark = pytest.mark.unit

_FEBRUARY = (date(2025, 2, 1), date(2025, 2, 28))


@pytest.mark.parametrize(
    "raw",
    [
        "01.02.2025 - 28.02.2025",
        "01.02.2025 – 28.02.2025",
        "01.02.2025 bis 28.02.2025",
        "Leistungszeitraum: 01.02.2025 - 28.02.2025",
        "1.2.–28.2.2025",
        "1.–28.2.2025",
        "du 1er au 28 février 2025",
        "dal 1 al 28 febbraio 2025",
        "2025-02-01 to 2025-02-28",
    ],
)
def test_a_range_of_days_is_read_in_every_form(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end) == _FEBRUARY
    assert parsed.precision == DatePrecision.DAY


def test_a_month_stands_for_the_whole_month() -> None:
    parsed = PeriodTextParser.parse("Februar 2025")

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (*_FEBRUARY, DatePrecision.MONTH)


def test_a_single_date_of_supply_is_a_one_day_period() -> None:
    parsed = PeriodTextParser.parse("Lieferdatum 14.03.2025")

    assert parsed is not None
    assert parsed.start == parsed.end == date(2025, 3, 14)


@pytest.mark.parametrize("raw", ["28.02.2025 - 01.02.2025", "laufend", None])
def test_a_reversed_range_or_no_date_is_no_period(raw: str | None) -> None:
    assert PeriodTextParser.parse(raw) is None


_FIRST_QUARTER = (date(2025, 1, 1), date(2025, 3, 31))


@pytest.mark.parametrize(
    "raw",
    [
        "1. Januar bis 31. März 2025",
        "1er janvier au 31 mars 2025",
        "dal 1 gennaio al 31 marzo 2025",
        "1 January – 31 March 2025",
        "January 1 – March 31, 2025",
        "1.1.–31.3.2025",
    ],
)
def test_a_range_whose_start_leaves_out_the_year_takes_it_from_the_end(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (*_FIRST_QUARTER, DatePrecision.DAY)


@pytest.mark.parametrize(
    "raw",
    [
        "Januar – März 2025",
        "Januar bis März 2025",
        "de janvier à mars 2025",
        "da gennaio a marzo 2025",
        "January – March 2025",
        "01.2025 – 03.2025",
    ],
)
def test_a_range_of_months_covers_every_month_at_month_precision(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (*_FIRST_QUARTER, DatePrecision.MONTH)


def test_a_range_of_months_may_cross_the_year() -> None:
    parsed = PeriodTextParser.parse("Dezember 2024 – Februar 2025")

    assert parsed is not None
    assert (parsed.start, parsed.end) == (date(2024, 12, 1), date(2025, 2, 28))


@pytest.mark.parametrize(
    "raw",
    ["Januar bis 31.03.2025", "März – Januar 2025", "Leistung 1. Februar 2025, Rechnung März 2025"],
)
def test_two_dates_in_no_form_read_here_store_no_period_rather_than_one_end(raw: str) -> None:
    assert PeriodTextParser.parse(raw) is None


@pytest.mark.parametrize("raw", ["1. Mai 2025", "14 March 2025"])
def test_one_date_written_with_its_month_name_is_still_one_date(raw: str) -> None:
    parsed = PeriodTextParser.parse(raw)

    assert parsed is not None
    assert parsed.start == parsed.end
