"""Dates as invoices in Switzerland, the EU and English-speaking countries write them, and the ones that must stay
unread because reading them would be a guess."""

from datetime import date

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.date_text_parser import DateTextParser

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "raw",
    [
        "14. März 2025",
        "14. Maerz 2025",
        "Zürich, 14. März 2025",
        "Freitag, 14. März 2025",
        "14.03.2025",
        "14.3.25",
        "14-03-2025",
        "2025-03-14",
        "14 mars 2025",
        "14 marzo 2025",
        "March 14, 2025",
        "14 March 2025",
        "14 Mar 2025",
        "14/03/2025",
        "03/14/2025",
        "Datum: 14.03.2025",
    ],
)
def test_a_day_in_any_supported_form_is_read(raw: str) -> None:
    parsed = DateTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (date(2025, 3, 14), date(2025, 3, 14), DatePrecision.DAY)


def test_a_french_first_of_the_month_is_read() -> None:
    parsed = DateTextParser.parse("1er mars 2025")

    assert parsed is not None
    assert parsed.start == date(2025, 3, 1)


@pytest.mark.parametrize(
    ("raw", "start", "end", "precision"),
    [
        ("März 2025", date(2025, 3, 1), date(2025, 3, 31), DatePrecision.MONTH),
        ("février 2025", date(2025, 2, 1), date(2025, 2, 28), DatePrecision.MONTH),
        ("02/2025", date(2025, 2, 1), date(2025, 2, 28), DatePrecision.MONTH),
        ("Q1 2025", date(2025, 1, 1), date(2025, 3, 31), DatePrecision.QUARTER),
        ("1. Quartal 2025", date(2025, 1, 1), date(2025, 3, 31), DatePrecision.QUARTER),
        ("2e trimestre 2025", date(2025, 4, 1), date(2025, 6, 30), DatePrecision.QUARTER),
        ("primo trimestre 2025", date(2025, 1, 1), date(2025, 3, 31), DatePrecision.QUARTER),
        ("2025", date(2025, 1, 1), date(2025, 12, 31), DatePrecision.YEAR),
    ],
)
def test_a_month_quarter_or_year_covers_all_its_days(
    raw: str, start: date, end: date, precision: DatePrecision
) -> None:
    parsed = DateTextParser.parse(raw)

    assert parsed is not None
    assert (parsed.start, parsed.end, parsed.precision) == (start, end, precision)


@pytest.mark.parametrize(
    "raw",
    [
        "03/04/2025",
        "31.02.2025",
        "Zahlbar innert 30 Tagen netto",
        "30 Tage netto",
        "sofort",
        "",
    ],
)
def test_an_ambiguous_impossible_or_relative_date_stays_unread(raw: str) -> None:
    assert DateTextParser.parse(raw) is None


def test_payment_terms_with_a_date_give_that_date() -> None:
    parsed = DateTextParser.parse("zahlbar bis 13.04.2025")

    assert parsed is not None
    assert parsed.start == date(2025, 4, 13)


def test_two_digit_years_before_70_are_this_century() -> None:
    assert DateTextParser.full_year("25") == 2025
    assert DateTextParser.full_year("99") == 1999
