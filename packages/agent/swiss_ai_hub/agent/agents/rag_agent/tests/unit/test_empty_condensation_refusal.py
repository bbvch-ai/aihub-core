"""A blank condensation refuses the turn with a localized message instead of leaking an exception.

`condense_standalone_question` raises `EmptyCondensationError` (#1753), and `stop_on_error` defaults to True,
so an uncaught raise reaches the dispatcher as an `ExceptionEvent` whose message the chat UI renders — the
raw English sentence from the error class. The conversation's `derive_query_step` catches it and returns the same
`RefusalStopEvent` shape the input-size guards use, so every "we cannot serve this turn" case looks alike.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ConversationContextualizedEvent,
    NotAMetaQuestionEvent,
    RefusalReason,
    RefusalStopEvent,
    StandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.core.generative_ai import EmptyCondensationError, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation

CONDENSE_PATH = "swiss_ai_hub.agent.capabilities.conversation.conversation.condense_standalone_question"


def _displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    displayer.display_chunk = AsyncMock()
    return displayer


def _config() -> RAGAgentConfig:
    return RAGAgentConfig(
        agent_id="condensation-test",
        name=LocaleString(en="Condensation"),
        description=LocaleString(en="Fixture"),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        retrievers=[],
    )


async def _run(displayer: MagicMock, locale: str = "en"):
    request = Conversation.contextualize(
        history=[
            ChatMessage(role=MessageRole.USER, content="Do we offer a discount?"),
            ChatMessage(role=MessageRole.USER, content="what about part-timers?"),
        ]
    )
    with patch.object(LLMConfig, "cost_reporting_llm") as cost_reporting_llm:
        cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=False)
        return await Conversation.derive_query_step(
            RAGAgent(),
            request=request,
            _cleared=NotAMetaQuestionEvent(reasoning="cleared"),
            conversation=_config(),
            displayer=displayer,
            t=LocaleHandler(locale=locale),
        )


@pytest.mark.asyncio
async def test_a_blank_condensation_becomes_a_refusal_stop_event():
    displayer = _displayer()

    with patch(CONDENSE_PATH, side_effect=EmptyCondensationError("nothing came back")):
        result = await _run(displayer)

    assert isinstance(result, RefusalStopEvent)
    assert result.reason == RefusalReason.CONDENSATION_EMPTY


@pytest.mark.asyncio
async def test_the_refusal_is_rendered_to_the_user_and_carries_the_same_text():
    """The chunk is what the chat renders; `output_messages` carries it for non-streaming consumers."""
    displayer = _displayer()

    with patch(CONDENSE_PATH, side_effect=EmptyCondensationError("nothing came back")):
        result = await _run(displayer)

    displayer.display_chunk.assert_awaited_once()
    assert displayer.display_chunk.await_args.args[0] == result.output_messages[-1].content


@pytest.mark.asyncio
async def test_the_refusal_is_localized_not_the_exception_text():
    """The point of the catch: the user must never see `EmptyCondensationError`'s English message."""
    rendered = {}
    for locale in ("en", "de", "fr", "it"):
        displayer = _displayer()
        with patch(CONDENSE_PATH, side_effect=EmptyCondensationError("nothing came back")):
            result = await _run(displayer, locale=locale)
        rendered[locale] = result.output_messages[-1].content

    assert "nothing came back" not in rendered.values()
    assert all(text for text in rendered.values())
    assert len(set(rendered.values())) == 4, f"locales must differ, got {rendered}"


@pytest.mark.asyncio
async def test_a_usable_condensation_still_returns_the_query_and_the_condenser_event():
    """The guard must not swallow the happy path."""
    displayer = _displayer()
    condensed = ChatMessage(role=MessageRole.USER, content="Do we offer a part-time discount?")

    with patch(CONDENSE_PATH, new=AsyncMock(return_value=condensed)):
        result = await _run(displayer)

    assert [type(event) for event in result] == [StandaloneQuestionCondenserEvent, ConversationContextualizedEvent]
    assert result[1].query == condensed.content
