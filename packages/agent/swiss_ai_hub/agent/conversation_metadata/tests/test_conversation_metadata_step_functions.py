from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import ConversationTitleEvent, FollowUpQuestionsEvent

from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import (
    TITLE_GENERATED_KEY,
    do_generate_follow_up_questions,
    do_generate_title,
    generate_conversation_metadata,
)
from swiss_ai_hub.agent.conversation_metadata.follow_up_questions_result import FollowUpQuestionsResult
from swiss_ai_hub.agent.conversation_metadata.title_result import TitleResult
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler


class FakeThreadContext:
    def __init__(self, store: dict | None = None):
        self._store = store or {}

    async def get(self, key, default=None):
        return self._store.get(key, default)

    async def set(self, key, value):
        self._store[key] = value


@pytest.fixture
def locale_handler() -> AgentLocaleHandler:
    return AgentLocaleHandler("en")


@pytest.fixture
def displayer() -> MagicMock:
    d = MagicMock()
    d.display_thought = AsyncMock()
    d.display_event = AsyncMock()
    d.display_llm_costs = AsyncMock()
    return d


def _llm_returning(result) -> MagicMock:
    llm = MagicMock()
    llm.astructured_predict = AsyncMock(return_value=result)
    return llm


def _llm_config(llm: MagicMock) -> MagicMock:
    config = MagicMock()

    @asynccontextmanager
    async def ctx(_displayer):
        yield llm

    config.cost_reporting_llm = ctx
    return config


def _conversation() -> list[ChatMessage]:
    return [
        ChatMessage(role=MessageRole.USER, content="What's the weather in Ho Chi Minh City?"),
        ChatMessage(role=MessageRole.ASSISTANT, content="It is hot and humid, around 33°C."),
    ]


def _emitted(displayer: MagicMock):
    return displayer.display_event.call_args.args[0]


@pytest.mark.asyncio
async def test_title_emitted_and_flag_set_first_time(displayer, locale_handler):
    thread_context = FakeThreadContext()
    llm = _llm_returning(TitleResult(title="Weather in Ho Chi Minh City"))

    await do_generate_title(_conversation(), _llm_config(llm), displayer, locale_handler, thread_context)

    displayer.display_event.assert_awaited_once()
    emitted = _emitted(displayer)
    assert isinstance(emitted, ConversationTitleEvent)
    assert emitted.title == "Weather in Ho Chi Minh City"
    assert await thread_context.get(TITLE_GENERATED_KEY) is True


@pytest.mark.asyncio
async def test_title_is_immutable_when_flag_set(displayer, locale_handler):
    thread_context = FakeThreadContext({TITLE_GENERATED_KEY: True})
    llm = _llm_returning(TitleResult(title="A Different Title"))

    await do_generate_title(_conversation(), _llm_config(llm), displayer, locale_handler, thread_context)

    displayer.display_event.assert_not_awaited()
    llm.astructured_predict.assert_not_called()


@pytest.mark.asyncio
async def test_title_deferred_when_no_topic(displayer, locale_handler):
    """A greeting-only turn yields no determinable title and leaves the flag unset for a retry."""
    thread_context = FakeThreadContext()
    llm = _llm_returning(TitleResult(title=None))

    await do_generate_title(
        [ChatMessage(role=MessageRole.USER, content="hello")],
        _llm_config(llm),
        displayer,
        locale_handler,
        thread_context,
    )

    displayer.display_event.assert_not_awaited()
    assert await thread_context.get(TITLE_GENERATED_KEY) is None


@pytest.mark.asyncio
async def test_follow_ups_emitted(displayer, locale_handler):
    llm = _llm_returning(FollowUpQuestionsResult(questions=["What is the forecast for tomorrow?"]))

    await do_generate_follow_up_questions(_conversation(), _llm_config(llm), displayer, locale_handler)

    displayer.display_event.assert_awaited_once()
    emitted = _emitted(displayer)
    assert isinstance(emitted, FollowUpQuestionsEvent)
    assert emitted.questions == ["What is the forecast for tomorrow?"]


@pytest.mark.asyncio
async def test_follow_ups_not_emitted_when_empty(displayer, locale_handler):
    llm = _llm_returning(FollowUpQuestionsResult(questions=[]))

    await do_generate_follow_up_questions(_conversation(), _llm_config(llm), displayer, locale_handler)

    displayer.display_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_metadata_uses_only_user_assistant_messages(displayer, locale_handler):
    """System prompts and tool turns (e.g. McpReactAgent noise) must be filtered before titling."""
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are an agent. Available tools: weather_lookup ..."),
        ChatMessage(role=MessageRole.USER, content="What's the weather in Ho Chi Minh City?"),
        ChatMessage(role=MessageRole.ASSISTANT, content=""),  # tool-call turn, no text
        ChatMessage(role=MessageRole.TOOL, content="weather_lookup(...) -> 33C"),
        ChatMessage(role=MessageRole.ASSISTANT, content="It is hot and humid, around 33°C."),
    ]
    llm = _llm_returning(TitleResult(title="Weather in Ho Chi Minh City"))

    await do_generate_title(messages, _llm_config(llm), displayer, locale_handler, FakeThreadContext())

    forwarded = llm.astructured_predict.call_args.kwargs["chat_history"]
    assert [m.role for m in forwarded] == [MessageRole.USER, MessageRole.ASSISTANT]
    assert all(str(m.content or "").strip() for m in forwarded)


@pytest.mark.asyncio
async def test_generate_metadata_is_best_effort_on_failure(displayer, locale_handler):
    """A failing generator must not propagate — metadata is non-essential and must never fail the run."""
    llm = MagicMock()
    llm.astructured_predict = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
    thread_context = FakeThreadContext()

    # Must not raise.
    await generate_conversation_metadata(_conversation(), _llm_config(llm), displayer, locale_handler, thread_context)

    displayer.display_event.assert_not_awaited()
    assert await thread_context.get(TITLE_GENERATED_KEY) is None
