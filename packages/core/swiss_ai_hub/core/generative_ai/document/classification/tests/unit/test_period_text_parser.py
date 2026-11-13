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
