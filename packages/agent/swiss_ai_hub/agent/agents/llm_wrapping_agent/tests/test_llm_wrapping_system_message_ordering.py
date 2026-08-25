"""
Regression guard for the 400 "System message must be at the beginning" from strict providers
(e.g. Qwen3.5 on Infomaniak): the agent's own system prompt used to land at index 1 whenever the
chat client supplied its own system message (OpenWebUI model prompt, bot PathEntity.system_message).

Pure unit test — limit_chat_history_step touches no infrastructure.
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import NotAMetaQuestionEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
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


async def _limited_history(chat_history: list[ChatMessage]) -> list[ChatMessage]:
    event = await LLMWrappingAgent().limit_chat_history_step(
        event=UserMessageEvent(messages=chat_history, user=fake_user(), locale="en"),
        agent_config=_config(),
        _clear=NotAMetaQuestionEvent(reasoning="forced normal"),
    )
    return event.limited_history


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
async def test_agent_system_prompt_leads_when_client_sends_none():
    history = await _limited_history([ChatMessage(role=MessageRole.USER, content="Tell me about Fight Club")])

    system_indices = [index for index, message in enumerate(history) if message.role == MessageRole.SYSTEM]
    assert system_indices == [0]
    assert history[0].content == "Respond briefly."
