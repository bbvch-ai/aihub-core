import time

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_pattern import KnowledgeContentPattern
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_limits import (
    KnowledgeContentSearchLimits,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_timeout_error import (
    KnowledgeContentSearchTimeoutError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget

pytestmark = pytest.mark.unit


def test_the_remaining_time_is_never_zero_milliseconds() -> None:
    """`maxTimeMS: 0` means no limit, so a nearly spent budget must still pass at least 1."""
    budget = KnowledgeSearchBudget(0.0009)

    assert budget.remaining_ms() == 1


def test_a_spent_budget_raises_with_advice() -> None:
    budget = KnowledgeSearchBudget(0.001)
    time.sleep(0.01)

    with pytest.raises(KnowledgeContentSearchTimeoutError, match="narrow it with a path glob"):
        budget.remaining_seconds()


def test_a_runaway_pattern_is_stopped_by_one_budget_for_all_lines() -> None:
    pattern = KnowledgeContentPattern(r"^(a|a)+$", is_regex=True)
    text = "\n".join("a" * 40 + "b" for _ in range(200))
    started = time.monotonic()

    with pytest.raises(KnowledgeContentSearchTimeoutError):
        pattern.matching_lines(text, KnowledgeContentSearchLimits(), KnowledgeSearchBudget(1))

    assert time.monotonic() - started < 1.5
