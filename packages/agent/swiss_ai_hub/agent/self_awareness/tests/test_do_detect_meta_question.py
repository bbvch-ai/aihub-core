from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.events.agent import MetaQuestionDetectedEvent, NotAMetaQuestionEvent

from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.self_awareness.meta_question_classification import MetaQuestionClassification
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import do_detect_meta_question


@pytest.fixture
def locale_handler() -> AgentLocaleHandler:
    return AgentLocaleHandler("en")


def _llm_returning(classification: MetaQuestionClassification) -> MagicMock:
    llm = MagicMock()
    llm.metadata.is_function_calling_model = True
    llm.astructured_predict = AsyncMock(return_value=classification)
    return llm


@pytest.fixture
def displayer() -> MagicMock:
    d = MagicMock()
    d.display_thought = AsyncMock()
    d.display_llm_costs = AsyncMock()
    return d


def _llm_config(llm: MagicMock) -> MagicMock:
    config = MagicMock()

    @asynccontextmanager
    async def ctx(_displayer):
        yield llm

    config.cost_reporting_llm = ctx
    return config


@pytest.mark.asyncio
async def test_meta_question_routes_to_detected_event(displayer, locale_handler):
    llm = _llm_returning(
        MetaQuestionClassification(is_meta_question=True, category="capabilities", reasoning="asks what it can do")
    )

    result = await do_detect_meta_question(
        user_query="What can you do?",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
    )

    assert isinstance(result, MetaQuestionDetectedEvent)
    assert result.category == "capabilities"
    assert result.user_query == "What can you do?"
    assert result.reasoning == "asks what it can do"
    displayer.display_thought.assert_awaited_once()


@pytest.mark.asyncio
async def test_normal_task_routes_to_gate_event(displayer, locale_handler):
    llm = _llm_returning(MetaQuestionClassification(is_meta_question=False, category=None, reasoning="domain question"))

    result = await do_detect_meta_question(
        user_query="What is the vacation policy?",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
    )

    assert isinstance(result, NotAMetaQuestionEvent)
    assert result.reasoning == "domain question"


@pytest.mark.asyncio
async def test_lookalike_task_is_not_meta(displayer, locale_handler):
    """A message that mentions "you"/"do" but asks about the data is a normal task."""
    llm = _llm_returning(
        MetaQuestionClassification(is_meta_question=False, category=None, reasoning="about the document, not the agent")
    )

    result = await do_detect_meta_question(
        user_query="What can I do with this document?",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
    )

    assert isinstance(result, NotAMetaQuestionEvent)


@pytest.mark.asyncio
async def test_meta_without_category_falls_back_to_gate(displayer, locale_handler):
    """Defensive: is_meta_question True but no category must not produce an invalid detected event."""
    llm = _llm_returning(MetaQuestionClassification(is_meta_question=True, category=None, reasoning="ambiguous"))

    result = await do_detect_meta_question(
        user_query="hmm",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
    )

    assert isinstance(result, NotAMetaQuestionEvent)
