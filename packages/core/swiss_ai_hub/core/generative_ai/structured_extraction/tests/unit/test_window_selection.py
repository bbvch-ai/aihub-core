import pytest

from swiss_ai_hub.core.generative_ai.structured_extraction.record_merger import RecordMerger
from swiss_ai_hub.core.generative_ai.structured_extraction.window_selection import WindowSelection

pytestmark = pytest.mark.unit


def test_a_document_that_fits_is_read_whole():
    assert WindowSelection.choose(["a", "b", "c"], 5) == [0, 1, 2]


def test_the_opening_and_the_windows_naming_the_row_terms_are_read_first():
    windows = ["header", "notes", "Laptop and Monitor", "terms", "Server rack", "notes", "Laptop"]

    assert WindowSelection.choose(windows, 3, "laptop|monitor|server") == [0, 2, 4]


def test_without_matching_terms_the_reading_is_spread_over_the_document():
    windows = [f"part {index}" for index in range(10)]

    assert WindowSelection.choose(windows, 4, "nowhere") == [0, 3, 6, 9]


def test_terms_that_are_not_a_valid_pattern_count_as_plain_words():
    windows = ["header", "price (net", "other", "more"]

    assert WindowSelection.choose(windows, 2, "price (net") == [0, 1]


def test_records_of_windows_that_are_not_neighbours_are_never_merged():
    line = {"item": "Laptop", "amount": 1450.0}

    assert len(RecordMerger.merge([[line], [line]], positions=[0, 1])) == 1
    assert len(RecordMerger.merge([[line], [line]], positions=[0, 7])) == 2


def test_copies_differing_only_in_their_match_mark_are_one_record_kept_as_a_match():
    unsure = {"item": "Docking station", "amount": 220.0, "record_match": "unsure"}
    sure = {"item": "Docking station", "amount": 220.0, "record_match": "yes"}

    assert RecordMerger.merge([[unsure], [sure]]) == [sure]
