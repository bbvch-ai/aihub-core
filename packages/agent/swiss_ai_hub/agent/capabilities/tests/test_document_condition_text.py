"""The document condition as the user and the judge read it: the user's words, then the period in words."""

from datetime import date

import pytest
from swiss_ai_hub.core.generative_ai import PathDateRange

from swiss_ai_hub.agent.capabilities.record_extraction.document_condition_text import DocumentConditionText
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
_YEAR_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))


def test_the_condition_comes_first_and_the_period_after_it() -> None:
    assert (
        DocumentConditionText.of("only contracts with Hooli", _YEAR_2025, T)
        == "only contracts with Hooli; dated between 2025-01-01 and 2025-12-31"
    )


def test_a_period_alone_or_a_condition_alone_stands_by_itself() -> None:
    assert DocumentConditionText.of(None, _YEAR_2025, T) == "dated between 2025-01-01 and 2025-12-31"
    assert DocumentConditionText.of("signed versions only", None, T) == "signed versions only"


def test_without_a_condition_or_a_period_there_is_no_text() -> None:
    assert DocumentConditionText.of(None, None, T) is None
    assert DocumentConditionText.of("", None, T) is None


def test_an_open_bound_is_worded_as_one_side() -> None:
    assert DocumentConditionText.period(PathDateRange(start=date(2025, 3, 1)), T) == "dated on or after 2025-03-01"
    assert DocumentConditionText.period(PathDateRange(end=date(2023, 12, 31)), T) == "dated on or before 2023-12-31"


def test_a_period_no_code_could_read_is_worded_as_written() -> None:
    assert DocumentConditionText.period_words("last spring", None, T) == "dated on or after last spring"
    assert DocumentConditionText.period_words(None, None, T) == ""


@pytest.mark.parametrize("locale", ["de", "en", "fr", "it"])
@pytest.mark.parametrize(("start", "end"), [("2025-01-01", "2025-12-31"), ("2025-03-01", None), (None, "2023-12-31")])
def test_every_locale_words_every_period(locale: str, start: str | None, end: str | None) -> None:
    words = DocumentConditionText.period_words(start, end, AgentLocaleHandler(locale))

    assert "%{" not in words
    assert all(bound in words for bound in (start, end) if bound)
