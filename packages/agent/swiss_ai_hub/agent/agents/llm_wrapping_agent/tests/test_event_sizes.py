"""No event that ends a turn grows with an attached file.

The broker refuses an event above its payload limit (1 MB in development) without an error the caller sees, and the run
then waits forever. A form of `____` blanks is cheap in tokens and long in characters, so it passes the token budget
and reached the completion and stop events whole, with every text serialized twice. The answer is faked the way
`EventDisplayer.display_llm_stream` returns it: with the prompt it was given as `input_messages`.
"""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ContextComposedEvent,
    ConversationContextualizedEvent,
    LLMEvent,
    Message,
    ToolLoopFinishedEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.agent.agents.universal_agent.universal_agent_config import UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation

# Well below the development broker's 1 MB `max_payload`: headers and the subject need room.
EVENT_LIMIT_BYTES = 400_000
CONVERSATION_MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation"
FORM = ("<tr><td>Name:</td><td>" + "_" * 180 + "</td></tr>\n") * 4300
QUESTION = "Which fields does the attached form ask me to fill in?"
REPLY = "Name, address, date of birth and signature."


def _size(event: Any) -> int:
    return len(event.model_dump_json(serialize_as_any=True).encode())


def _prompt() -> list[ChatMessage]:
    return [
        ChatMessage(role=MessageRole.SYSTEM, content=f"Respond briefly.\n\n<attached_file>\n{FORM}</attached_file>"),
        ChatMessage(role=MessageRole.USER, content="Hello"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Hi, how can I help?"),
        ChatMessage(role=MessageRole.USER, content=QUESTION),
    ]


def _answer_to(messages: list[ChatMessage]) -> LLMEvent:
    return LLMEvent(
        input_messages=[Message.from_llama_index(message) for message in messages],
        output_messages=[Message.from_string(role="assistant", content=REPLY, name="m")],
        chat_model_name="m",
    )


async def _stop_after(completion: Any) -> Any:
    with patch(f"{CONVERSATION_MODULE}.generate_follow_up_questions", new=AsyncMock()):
        return await Conversation.complete_conversation_step(
            LLMWrappingAgent(),
            request=completion,
            conversation=_wrapping_config(),
            displayer=MagicMock(),
            t=MagicMock(),
        )


def _wrapping_config() -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="event-sizes",
        name=LocaleString(en="Event sizes"),
        description=LocaleString(en="Event sizes fixture"),
        system_prompt=LocaleString(en="Respond briefly."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
    )


def test_the_prompt_alone_would_not_fit():
    assert _size(_answer_to(_prompt())) > 1_048_576


@pytest.mark.asyncio
async def test_the_llm_wrapping_turn_ends_in_events_the_broker_accepts():
    composed = ContextComposedEvent(history=_prompt())
    displayer = MagicMock()
    displayer.display_llm_stream = AsyncMock(side_effect=lambda _config, _llm, messages, **_: _answer_to(messages))

    @asynccontextmanager
    async def _llm(*_args, **_kwargs):
        yield MagicMock()

    with patch.object(LLMConfig, "cost_reporting_llm", _llm):
        events = await LLMWrappingAgent().respond_step(
            event=composed,
            ctx=ConversationContextualizedEvent(history=composed.history, query=QUESTION),
            agent_config=_wrapping_config(),
            displayer=displayer,
            topic=MagicMock(),
            t=LocaleHandler(locale="en"),
        )
    stop = await _stop_after(events[-1])

    for event in [*events, stop]:
        assert _size(event) < EVENT_LIMIT_BYTES, type(event).__name__
    assert [message.content for message in stop.input_messages] == ["Hello", "Hi, how can I help?", QUESTION]
    assert stop.output_messages[-1].content == REPLY


@pytest.mark.asyncio
async def test_the_universal_turn_ends_in_events_the_broker_accepts():
    config = UniversalAgentConfig(
        agent_id="event-sizes",
        name=LocaleString(en="Universal"),
        description=LocaleString(en="Universal fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
    )
    ctx = ConversationContextualizedEvent(history=_prompt(), query=QUESTION)

    events = await UniversalAgent().complete_step(
        ToolLoopFinishedEvent(answer=_answer_to(_prompt())),
        ctx,
        agent_config=config,
        topic=MagicMock(),
        t=LocaleHandler(locale="en"),
        user=None,
    )
    stop = await _stop_after(events[-1])

    for event in [*events, stop]:
        assert _size(event) < EVENT_LIMIT_BYTES, type(event).__name__
