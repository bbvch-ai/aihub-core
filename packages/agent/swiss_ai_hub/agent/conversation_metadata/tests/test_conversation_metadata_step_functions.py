from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ConversationTagsEvent,
    ConversationTitleEvent,
    SuggestedFollowUpQuestionsEvent,
)

from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import (
    CONVERSATION_TITLE_KEY,
    do_generate_tags,
    do_generate_title,
    do_generate_title_once,
    do_suggest_follow_up_questions,
)
from swiss_ai_hub.agent.conversation_metadata.follow_up_questions_result import FollowUpQuestionsResult
from swiss_ai_hub.agent.conversation_metadata.tags_result import TagsResult
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
    d.display_llm_costs = AsyncMock()
    return d


def _llm_returning(result) -> MagicMock:
    llm = MagicMock()
    llm.metadata.is_function_calling_model = True
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


@pytest.mark.asyncio
async def test_generate_title_returns_event(displayer, locale_handler):
    llm = _llm_returning(TitleResult(title="Weather in Ho Chi Minh City"))

    result = await do_generate_title(_conversation(), _llm_config(llm), displayer, locale_handler)

    assert isinstance(result, ConversationTitleEvent)
    assert result.title == "Weather in Ho Chi Minh City"
    displayer.display_thought.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_title_defers_when_no_topic(displayer, locale_handler):
    """A greeting-only turn yields no determinable title."""
    llm = _llm_returning(TitleResult(title=None))

    result = await do_generate_title(
        [ChatMessage(role=MessageRole.USER, content="hello")], _llm_config(llm), displayer, locale_handler
    )

    assert result is None


@pytest.mark.asyncio
async def test_generate_title_once_stores_and_emits_first_time(displayer, locale_handler):
    thread_context = FakeThreadContext()
    llm = _llm_returning(TitleResult(title="Weather in Ho Chi Minh City"))

    result = await do_generate_title_once(_conversation(), thread_context, _llm_config(llm), displayer, locale_handler)

    assert isinstance(result, ConversationTitleEvent)
    assert await thread_context.get(CONVERSATION_TITLE_KEY) == "Weather in Ho Chi Minh City"


@pytest.mark.asyncio
async def test_generate_title_once_is_immutable_when_already_set(displayer, locale_handler):
    thread_context = FakeThreadContext({CONVERSATION_TITLE_KEY: "Existing Title"})
    llm = _llm_returning(TitleResult(title="A Different Title"))

    result = await do_generate_title_once(_conversation(), thread_context, _llm_config(llm), displayer, locale_handler)

    assert result is None
    llm.astructured_predict.assert_not_called()
    assert await thread_context.get(CONVERSATION_TITLE_KEY) == "Existing Title"


@pytest.mark.asyncio
async def test_generate_title_once_does_not_store_when_undeterminable(displayer, locale_handler):
    thread_context = FakeThreadContext()
    llm = _llm_returning(TitleResult(title=None))

    result = await do_generate_title_once(
        [ChatMessage(role=MessageRole.USER, content="hello")],
        thread_context,
        _llm_config(llm),
        displayer,
        locale_handler,
    )

    assert result is None
    assert await thread_context.get(CONVERSATION_TITLE_KEY) is None


@pytest.mark.asyncio
async def test_generate_tags_returns_event(displayer, locale_handler):
    llm = _llm_returning(TagsResult(tags=["Weather", "Travel"]))

    result = await do_generate_tags(_conversation(), _llm_config(llm), displayer, locale_handler)

    assert isinstance(result, ConversationTagsEvent)
    assert result.tags == ["Weather", "Travel"]


@pytest.mark.asyncio
async def test_generate_tags_returns_none_when_empty(displayer, locale_handler):
    llm = _llm_returning(TagsResult(tags=[]))

    result = await do_generate_tags(_conversation(), _llm_config(llm), displayer, locale_handler)

    assert result is None


@pytest.mark.asyncio
async def test_suggest_follow_ups_returns_event(displayer, locale_handler):
    llm = _llm_returning(FollowUpQuestionsResult(questions=["What is the forecast for tomorrow?"]))

    result = await do_suggest_follow_up_questions(_conversation(), _llm_config(llm), displayer, locale_handler)

    assert isinstance(result, SuggestedFollowUpQuestionsEvent)
    assert result.questions == ["What is the forecast for tomorrow?"]


@pytest.mark.asyncio
async def test_suggest_follow_ups_returns_none_when_empty(displayer, locale_handler):
    llm = _llm_returning(FollowUpQuestionsResult(questions=[]))

    result = await do_suggest_follow_up_questions(_conversation(), _llm_config(llm), displayer, locale_handler)

    assert result is None
