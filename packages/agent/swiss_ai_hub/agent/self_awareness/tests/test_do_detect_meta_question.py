from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from openai import APITimeoutError
from swiss_ai_hub.core.events.agent import MetaQuestionDetectedEvent, NotAMetaQuestionEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import do_detect_meta_question


@pytest.fixture
def locale_handler() -> AgentLocaleHandler:
    return AgentLocaleHandler("en")


def _llm_returning(label: str) -> MagicMock:
    """Detection classifies via a plain-text label token; mock the chat response that carries it."""
    llm = MagicMock()
    llm.metadata.is_function_calling_model = True
    response = ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=label))
    llm.achat = AsyncMock(return_value=response)
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
    async def ctx(_displayer, user=None):  # noqa: ARG001
        yield llm

    config.cost_reporting_llm = ctx
    return config


@pytest.mark.asyncio
async def test_meta_question_routes_to_detected_event(displayer, locale_handler):
    llm = _llm_returning("META_CAPABILITIES")

    result = await do_detect_meta_question(
        user_query="What can you do?",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )

    assert isinstance(result, MetaQuestionDetectedEvent)
    assert result.category == "capabilities"
    assert result.user_query == "What can you do?"
    displayer.display_thought.assert_awaited_once()


@pytest.mark.asyncio
async def test_normal_task_routes_to_gate_event(displayer, locale_handler):
    llm = _llm_returning("NORMAL")

    result = await do_detect_meta_question(
        user_query="What is the vacation policy?",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )

    assert isinstance(result, NotAMetaQuestionEvent)


@pytest.mark.asyncio
async def test_lookalike_task_is_not_meta(displayer, locale_handler):
    """A message that mentions "you"/"do" but asks about the data is a normal task."""
    llm = _llm_returning("NORMAL")

    result = await do_detect_meta_question(
        user_query="What can I do with this document?",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )

    assert isinstance(result, NotAMetaQuestionEvent)


@pytest.mark.asyncio
async def test_unrecognized_label_falls_back_to_gate(displayer, locale_handler):
    """An unparseable classification (no known token) must not crash; degrade to a normal task."""
    llm = _llm_returning("I am not sure how to classify this.")

    result = await do_detect_meta_question(
        user_query="hmm",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )

    assert isinstance(result, NotAMetaQuestionEvent)
    assert "unrecognized classification" in result.reasoning


@pytest.mark.asyncio
async def test_transport_error_falls_back_to_gate(displayer, locale_handler):
    """Detection gates every message: a transient gateway error must degrade to a normal task, not
    escape as an ExceptionEvent that would kill an otherwise-healthy run."""
    llm = _llm_returning("NORMAL")
    llm.achat = AsyncMock(side_effect=APITimeoutError(request=MagicMock()))

    result = await do_detect_meta_question(
        user_query="What is the vacation policy?",
        llm_config=_llm_config(llm),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )

    assert isinstance(result, NotAMetaQuestionEvent)
    assert "detection call failed" in result.reasoning


@pytest.mark.asyncio
async def test_degraded_fallback_is_distinguishable_from_a_genuine_normal_verdict(displayer, locale_handler):
    """A silently-failing classifier used to be indistinguishable from a working one in the event log."""
    verdict = await do_detect_meta_question(
        user_query="What is the vacation policy?",
        llm_config=_llm_config(_llm_returning("NORMAL")),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )
    degraded = await do_detect_meta_question(
        user_query="What is the vacation policy?",
        llm_config=_llm_config(_llm_returning("no idea")),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )

    assert verdict.reasoning != degraded.reasoning


@pytest.mark.parametrize(
    ("label", "category"),
    [
        ("META_IDENTITY", "identity"),
        ("META_CAPABILITIES", "capabilities"),
        ("META_BEHAVIOR", "behavior"),
    ],
)
@pytest.mark.asyncio
async def test_every_meta_label_maps_to_its_category(label, category, displayer, locale_handler):
    result = await do_detect_meta_question(
        user_query="who are you?",
        llm_config=_llm_config(_llm_returning(label)),
        displayer=displayer,
        t=locale_handler,
        user=fake_user(),
    )

    assert isinstance(result, MetaQuestionDetectedEvent)
    assert result.category == category


@pytest.mark.asyncio
async def test_a_query_past_the_context_window_skips_the_classification_call(displayer, locale_handler):
    """Detection gates every chat message, so a query that cannot be classified must not be sent at all.
    Entering `cost_reporting_llm` mints a per-user gateway key over HTTP before the doomed call is even
    made (aihub-core-private#241), and the failure it degrades to names the wrong cause.
    """
    llm_config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
    entered = False

    @asynccontextmanager
    async def must_not_be_entered(_displayer, user=None):  # noqa: ARG001
        nonlocal entered
        entered = True
        yield MagicMock()

    with patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 100_000}}):
        object.__setattr__(llm_config, "cost_reporting_llm", must_not_be_entered)
        result = await do_detect_meta_question(
            user_query=" hello" * 200_000,
            llm_config=llm_config,
            displayer=displayer,
            t=locale_handler,
            user=fake_user(),
        )

    assert isinstance(result, NotAMetaQuestionEvent)
    assert "context window" in result.reasoning
    assert not entered, "the classification call was made for a query that cannot fit"
