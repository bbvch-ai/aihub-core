import pytest

from swiss_ai_hub.core.generative_ai.structured_extraction.record_merger import RecordMerger

pytestmark = pytest.mark.unit


def test_single_window_keeps_identical_records() -> None:
    line = {"description": "Cable", "amount": 5.0}

    assert RecordMerger.merge([[line, dict(line)]]) == [line, line]


def test_record_repeated_in_the_overlap_of_adjacent_windows_is_kept_once() -> None:
    first = [{"description": "Laptop", "amount": 1200.0}, {"description": "Dock", "amount": 200.0}]
    second = [{"description": "Dock", "amount": 200.0}, {"description": "Monitor", "amount": 300.0}]

    merged = RecordMerger.merge([first, second])

    assert [record["description"] for record in merged] == ["Laptop", "Dock", "Monitor"]


def test_identical_records_in_non_adjacent_windows_are_both_kept() -> None:
    line = {"description": "Cable", "amount": 5.0}

    merged = RecordMerger.merge([[line], [{"description": "Other", "amount": 1.0}], [dict(line)]])

    assert len(merged) == 3


def test_duplicate_missing_header_fields_is_merged_and_fills_the_gaps() -> None:
    with_header = [{"invoice_number": "INV-7", "description": "Dock", "amount": None}]
    without_header = [{"invoice_number": None, "description": "Dock", "amount": 200.0}]

    merged = RecordMerger.merge([with_header, without_header])

    assert merged == [{"invoice_number": "INV-7", "description": "Dock", "amount": 200.0}]


def test_string_comparison_ignores_case_and_surrounding_whitespace() -> None:
    merged = RecordMerger.merge([[{"description": "Dock "}], [{"description": "dock"}]])

    assert len(merged) == 1


def test_conflicting_values_are_not_merged() -> None:
    merged = RecordMerger.merge(
        [[{"description": "Dock", "amount": 200.0}], [{"description": "Dock", "amount": 210.0}]]
    )

    assert len(merged) == 2


def test_two_real_repeats_in_an_overlap_both_survive() -> None:
    line = {"description": "Cable", "amount": 5.0}

    merged = RecordMerger.merge([[line, dict(line)], [dict(line), dict(line), dict(line)]])

    assert len(merged) == 3


def test_records_sharing_no_known_value_are_not_merged() -> None:
    merged = RecordMerger.merge([[{"a": "x", "b": None}], [{"a": None, "b": "y"}]])

    assert len(merged) == 2


def test_merge_does_not_mutate_the_input() -> None:
    first = [{"description": "Dock", "amount": None}]
    second = [{"description": "Dock", "amount": 200.0}]

    RecordMerger.merge([first, second])

    assert first == [{"description": "Dock", "amount": None}]
