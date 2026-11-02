from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_line import KnowledgeContentLine
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_match import KnowledgeContentMatch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_limits import (
    KnowledgeContentSearchLimits,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_result import (
    KnowledgeContentSearchResult,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair

pytestmark = pytest.mark.unit

_LONG = "a" * 1000 + "MATCH" + "b" * 1000


def test_a_short_line_is_returned_whole() -> None:
    line = KnowledgeContentLine.from_text("x\nshort line\ny", 2, 12, 2, 8, 240)

    assert (line.text, line.start, line.end, line.clipped) == ("short line", 2, 12, False)


@pytest.mark.parametrize(
    ("match_start", "expected_start"),
    [(0, 0), (1000, 1000 - 60), (2000, 2005 - 240)],
)
def test_a_long_line_is_clipped_to_a_window_around_the_match(match_start: int, expected_start: int) -> None:
    line = KnowledgeContentLine.from_text(_LONG, 0, len(_LONG), 1, match_start, 240)

    assert (line.start, line.end, line.clipped) == (expected_start, expected_start + 240, True)
    assert line.text == _LONG[line.start : line.end]


def test_lines_and_pages_report_what_was_left_out() -> None:
    summary = KnowledgeDocumentSummary(
        id="d1",
        collection=BucketNamespacePair(bucket_name="b", namespace_name="n"),
        path="a.md",
        filename="a.md",
        title="a.md",
        file_type="md",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    line = KnowledgeContentLine(line_number=1, start=0, end=1, text="x", clipped=False)
    match = KnowledgeContentMatch(summary=summary, lines=[line], matching_line_count=3)

    assert match.lines_truncated is True
    assert KnowledgeContentSearchResult(matches=[match], total_documents=1, next_offset=None).truncated is False
    assert KnowledgeContentSearchResult(matches=[match], total_documents=9, next_offset=1).truncated is True


@pytest.mark.parametrize(
    "limits",
    [
        {"max_documents": 0},
        {"max_documents": 101},
        {"max_lines_per_document": 51},
        {"max_line_chars": 39},
        {"timeout_seconds": 0},
        {"timeout_seconds": 31},
    ],
)
def test_limits_outside_their_bounds_are_rejected(limits: dict[str, float]) -> None:
    with pytest.raises(ValidationError):
        KnowledgeContentSearchLimits(**limits)
