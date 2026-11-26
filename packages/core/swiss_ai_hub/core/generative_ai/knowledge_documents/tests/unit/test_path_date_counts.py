import json
from datetime import date

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision
from swiss_ai_hub.core.generative_ai.document.classification.normalized_date import NormalizedDate
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_counts import PathDateCounts
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_verdict import PathDateVerdict

pytestmark = pytest.mark.unit

_YEAR_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))


def _year(year: int) -> NormalizedDate:
    return NormalizedDate(start=date(year, 1, 1), end=date(year, 12, 31), precision=DatePrecision.YEAR)


def _outside(path: str, year: int) -> tuple[str, NormalizedDate | None, PathDateVerdict]:
    return path, _year(year), PathDateVerdict.OUTSIDE


def test_each_verdict_is_counted() -> None:
    counts = PathDateCounts.collect(
        [
            ("2025/a.pdf", _year(2025), PathDateVerdict.WITHIN),
            ("x/b.pdf", _year(2025), PathDateVerdict.OVERLAPPING),
            _outside("2024/c.pdf", 2024),
            ("d.pdf", None, PathDateVerdict.UNDATED),
            ("e.pdf", None, PathDateVerdict.UNDATED),
        ],
        _YEAR_2025,
    )

    assert (counts.in_range, counts.excluded, counts.undated, counts.total) == (2, 1, 2, 5)
    assert counts.outside_years == [2024]
    assert counts.excluded_examples == ["2024/c.pdf"]


def test_an_outside_span_adds_every_year_it_crosses() -> None:
    span = NormalizedDate(start=date(2023, 12, 1), end=date(2024, 2, 29), precision=DatePrecision.DAY)

    counts = PathDateCounts.collect([("x.pdf", span, PathDateVerdict.OUTSIDE)], _YEAR_2025)

    assert counts.outside_years == [2023, 2024]


def test_only_the_years_nearest_the_period_are_kept_sorted() -> None:
    outcomes = [_outside(f"{year}/a.pdf", year) for year in range(2005, 2025)] + [_outside("2026/a.pdf", 2026)]

    counts = PathDateCounts.collect(outcomes, _YEAR_2025)

    assert counts.outside_years == [*range(2014, 2025), 2026]


def test_examples_are_capped_by_count() -> None:
    counts = PathDateCounts.collect([_outside(f"2024/{index}.pdf", 2024) for index in range(30)], _YEAR_2025)

    assert counts.excluded == 30
    assert counts.excluded_examples == [f"2024/{index}.pdf" for index in range(10)]


def test_examples_are_capped_by_serialized_bytes() -> None:
    path = "2024/" + "ä" * 150 + ".pdf"

    counts = PathDateCounts.collect([_outside(path, 2024) for _ in range(10)], _YEAR_2025)

    assert len(counts.excluded_examples) == 2
    assert sum(len(json.dumps(example)) for example in counts.excluded_examples) <= 2_000


def test_a_long_path_is_cut_and_still_taken_first() -> None:
    path = "2024/" + "é" * 1_000 + ".pdf"

    counts = PathDateCounts.collect([_outside(path, 2024)], _YEAR_2025)

    assert counts.excluded_examples == [path[:199] + "…"]
