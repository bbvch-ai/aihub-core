"""
Regression guard for the 400 "System message must be at the beginning" from strict providers
(e.g. Qwen3.5 on Infomaniak): the agent's own system prompt used to land at index 1 whenever the
chat client supplied its own system message (OpenWebUI model prompt, bot PathEntity.system_message).

Pure unit test — limit_chat_history_step touches no infrastructure. The model-window lookup it now makes is a
real HTTP GET against LiteLLM, so it is patched here rather than left to fail open over the network.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ContextComposedEvent,
    ConversationContextualizedEvent,
    LLMEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig


def _config() -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="system_message_ordering_test",
        name=LocaleString(en="Test LLM Wrapper"),
        description=LocaleString(en="A test llm wrapping agent."),
        system_prompt=LocaleString(en="Respond briefly."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
    )


def _displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    displayer.display_chunk = AsyncMock()
    return displayer


async def _limited_history(chat_history: list[ChatMessage]) -> list[ChatMessage]:
    with patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 100_000}}):
        event = await LLMWrappingAgent().limit_chat_history_step(
            event=UserMessageEvent(messages=chat_history, user=fake_user(), locale="en"),
            agent_config=_config(),
            displayer=_displayer(),
            t=LocaleHandler(locale="en"),
        )
    return event.history


@async_test
async def test_client_system_prompt_does_not_displace_the_agent_system_prompt():
    history = await _limited_history(
        [
            ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            ChatMessage(role=MessageRole.USER, content="Tell me about Fight Club"),
        ]
    )

    system_indices = [index for index, message in enumerate(history) if message.role == MessageRole.SYSTEM]
    assert system_indices == [0], f"system messages must collapse into index 0, got {system_indices}"
    assert "You are a helpful assistant." in history[0].content
    assert "Respond briefly." in history[0].content


@async_test
async def test_recalled_memory_reaches_the_model_inside_the_leading_system_message():
    composed = ContextComposedEvent(
        history=[
            ChatMessage(role=MessageRole.SYSTEM, content="Respond briefly."),
            ChatMessage(role=MessageRole.SYSTEM, content="<user_context>The user leads Project Falcon.</user_context>"),
            ChatMessage(role=MessageRole.USER, content="Which project do I lead?"),
        ]
    )
    displayer = _displayer()
    displayer.display_llm_stream = AsyncMock(return_value=LLMEvent())

    @asynccontextmanager
    async def _llm(*_args, **_kwargs):
        yield MagicMock()

    with patch.object(LLMConfig, "cost_reporting_llm", _llm):
        await LLMWrappingAgent().respond_step(
            event=composed,
            ctx=ConversationContextualizedEvent(history=composed.history, query="Which project do I lead?"),
            agent_config=_config(),
            displayer=displayer,
            topic=MagicMock(),
            t=LocaleHandler(locale="en"),
        )

    sent = displayer.display_llm_stream.await_args.args[2]
    assert [message.role for message in sent] == [MessageRole.SYSTEM, MessageRole.USER]
    assert "Respond briefly." in sent[0].content
    assert "Project Falcon" in sent[0].content


@async_test
async def test_agent_system_prompt_leads_when_client_sends_none():
    history = await _limited_history([ChatMessage(role=MessageRole.USER, content="Tell me about Fight Club")])

    system_indices = [index for index, message in enumerate(history) if message.role == MessageRole.SYSTEM]
    assert system_indices == [0]
    assert history[0].content == "Respond briefly."
