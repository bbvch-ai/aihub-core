from typing import ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.chat_history.limit_chat_history import limit_chat_history
from aihub_lib.nats.events import LimitChatHistoryEvent, LLMStopEvent, UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig
from aihub_agent.i18n.AgentLocaleString import AgentLocaleString
from aihub_agent.workflow.decorators.step import step


class LLMWrappingAgent(Agent):
    """A simple agent that wraps an LLM and streams responses to user messages."""

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.llm_wrapping_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:message"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.limit_chat_history.name"),
        description=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.limit_chat_history.description"),
        icon="mage:edit",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: LLMWrappingAgentConfig,
    ) -> LimitChatHistoryEvent:
        """Truncates incoming chat messages to fit within the configured token limit"""
        locale = event.locale
        system_messages = [msg for msg in event.messages if msg.role == MessageRole.SYSTEM]
        system_prompt = ChatMessage(role=MessageRole.SYSTEM, content=agent_config.system_prompt.in_locale(locale))
        regular_messages = [msg for msg in event.messages if msg.role != MessageRole.SYSTEM]
        chat_history = [
            *system_messages,
            system_prompt,
            *regular_messages,
        ]
        limited_chat_history = limit_chat_history(
            chat_history=chat_history,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.start.name"),
        description=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.start.description"),
        icon="mage:message",
    )
    async def start_step(
        self,
        event: LimitChatHistoryEvent,
        agent_config: LLMWrappingAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMStopEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.limited_history, as_stop_step=True)
