"""
Regression guard for the 400 "System message must be at the beginning" from strict providers
(e.g. Qwen3.5 on Infomaniak): the agent's own few-shot system prompt used to land at index 1
whenever the chat client supplied its own system message (OpenWebUI model prompt, bot
PathEntity.system_message).

Pure unit test — create_few_shot_examples touches no infrastructure.
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import LimitChatHistoryEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import FewShotExample, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_standalone_question_condenser_event import (
    FewShotStandaloneQuestionCondenserEvent,
)
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.steps.prompting.few_shot_step.few_shot_step_config import FewShotStepConfig


def _config() -> FewShotAgentConfig:
    return FewShotAgentConfig(
        agent_id="system_message_ordering_test",
        name=LocaleString(en="Test FewShot"),
        description=LocaleString(en="A test few-shot agent."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        few_shot=FewShotStepConfig(
            few_shot_examples=[FewShotExample(user=LocaleString(en="hi"), agent=LocaleString(en="hello"))],
            system_prompt=LocaleString(en="Respond briefly."),
        ),
    )


async def _build_context(chat_history: list[ChatMessage]) -> list[ChatMessage]:
    event = await FewShotAgent().create_few_shot_examples(
        event=FewShotStandaloneQuestionCondenserEvent(
            condensed_chat_message=ChatMessage(role=MessageRole.USER, content="What is Fight Club about?")
        ),
        start_event=UserMessageEvent(messages=chat_history, user=fake_user(), locale="en"),
        chat_history_event=LimitChatHistoryEvent(limited_history=chat_history),
        agent_config=_config(),
    )
    return event.full_context


@async_test
async def test_client_system_prompt_does_not_displace_the_agent_system_prompt():
    context = await _build_context(
        [
            ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            ChatMessage(role=MessageRole.USER, content="Tell me about Fight Club"),
        ]
    )

    system_indices = [index for index, message in enumerate(context) if message.role == MessageRole.SYSTEM]
    assert system_indices == [0], f"system messages must collapse into index 0, got {system_indices}"
    assert "You are a helpful assistant." in context[0].content
    assert "Respond briefly." in context[0].content


@async_test
async def test_agent_system_prompt_leads_when_client_sends_none():
    context = await _build_context([ChatMessage(role=MessageRole.USER, content="Tell me about Fight Club")])

    system_indices = [index for index, message in enumerate(context) if message.role == MessageRole.SYSTEM]
    assert system_indices == [0]
    assert context[0].content == "Respond briefly."
    assert context[-1].role == MessageRole.USER
