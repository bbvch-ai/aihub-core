from datetime import date

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_verdict import PathDateVerdict

pytestmark = pytest.mark.unit

TODAY = date(2026, 11, 20)
_YEAR_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))


def _dated(start: date, end: date) -> NormalizedDate:
    return NormalizedDate(start=start, end=end, precision=DatePrecision.DAY)


def test_a_written_period_reads_iso_days() -> None:
    assert PathDateRange.written("2025-01-01", "2025-12-31") == _YEAR_2025


def test_a_written_bound_coarser_than_a_day_takes_its_first_or_last_day() -> None:
    assert PathDateRange.written("2025", "2025") == _YEAR_2025
    assert PathDateRange.written("März 2025", None) == PathDateRange(start=date(2025, 3, 1))
    assert PathDateRange.written("2025-03", "2025-04") == PathDateRange(start=date(2025, 3, 1), end=date(2025, 4, 30))


@pytest.mark.parametrize(("start", "end"), [(None, None), ("", " "), (None, "")])
def test_no_written_bound_is_no_period(start: str | None, end: str | None) -> None:
    assert PathDateRange.written(start, end) is None


def test_a_bound_that_names_no_date_raises() -> None:
    with pytest.raises(ValueError, match="names no date"):
        PathDateRange.written("last year", None)


def test_a_reversed_period_raises() -> None:
    with pytest.raises(ValueError, match="after its end"):
        PathDateRange.written("2025-12-31", "2025-01-01")


def test_a_period_needs_a_bound() -> None:
    with pytest.raises(ValidationError):
        PathDateRange()


@pytest.mark.parametrize(
    ("dated", "verdict"),
    [
        (_dated(date(2024, 1, 1), date(2024, 12, 31)), PathDateVerdict.OUTSIDE),
        (_dated(date(2026, 1, 1), date(2026, 1, 1)), PathDateVerdict.OUTSIDE),
        (_dated(date(2024, 12, 1), date(2025, 1, 31)), PathDateVerdict.OVERLAPPING),
        (_dated(date(2025, 3, 1), date(2025, 3, 31)), PathDateVerdict.WITHIN),
        (_dated(date(2025, 1, 1), date(2025, 1, 1)), PathDateVerdict.WITHIN),
        (_dated(date(2025, 12, 31), date(2025, 12, 31)), PathDateVerdict.WITHIN),
        (_dated(date(2024, 12, 31), date(2024, 12, 31)), PathDateVerdict.OUTSIDE),
        (None, PathDateVerdict.UNDATED),
    ],
)
def test_a_path_date_is_outside_overlapping_within_or_undated(
    dated: NormalizedDate | None, verdict: PathDateVerdict
) -> None:
    assert _YEAR_2025.verdict_of(dated) is verdict


def test_an_open_bound_never_ends() -> None:
    since_march = PathDateRange(start=date(2025, 3, 1))
    before_2024 = PathDateRange(end=date(2023, 12, 31))

    assert since_march.verdict_of(_dated(date(2030, 1, 1), date(2030, 1, 1))) is PathDateVerdict.WITHIN
    assert since_march.verdict_of(_dated(date(2025, 2, 1), date(2025, 2, 28))) is PathDateVerdict.OUTSIDE
    assert before_2024.verdict_of(_dated(date(1999, 1, 1), date(1999, 1, 1))) is PathDateVerdict.WITHIN
    assert before_2024.verdict_of(_dated(date(2023, 1, 1), date(2024, 12, 31))) is PathDateVerdict.OVERLAPPING


def test_the_verdict_of_a_path_reads_its_date() -> None:
    assert _YEAR_2025.verdict("invoices/2025/03/a.pdf", TODAY) is PathDateVerdict.WITHIN
    assert _YEAR_2025.verdict("invoices/2024/a.pdf", TODAY) is PathDateVerdict.OUTSIDE
    assert _YEAR_2025.verdict("Kontoauszug_01.12.2024-31.01.2025.pdf", TODAY) is PathDateVerdict.OVERLAPPING
    assert _YEAR_2025.verdict("contracts/acme.pdf", TODAY) is PathDateVerdict.UNDATED


def test_the_distance_to_a_year_counts_the_years_between() -> None:
    assert _YEAR_2025.distance_to(2025) == 0
    assert _YEAR_2025.distance_to(2022) == 3
    assert _YEAR_2025.distance_to(2027) == 2
    assert PathDateRange(start=date(2025, 3, 1)).distance_to(2040) == 0
    assert PathDateRange(end=date(2023, 12, 31)).distance_to(1990) == 0


def test_bounds_dump_as_iso_days_in_python_mode_and_keep_a_date_schema() -> None:
    assert _YEAR_2025.model_dump() == {"start": "2025-01-01", "end": "2025-12-31"}
    assert PathDateRange(end=date(2025, 3, 31)).model_dump() == {"start": None, "end": "2025-03-31"}
    end_schema = PathDateRange.model_json_schema(mode="serialization")["properties"]["end"]
    assert {"type": "string", "format": "date"} in end_schema["anyOf"]
