from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    LimitChatHistoryEvent,
    LLMStopEvent,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import limit_chat_history
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import (
    generate_conversation_metadata,
)
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.self_awareness.meta_question_workflow_summary import summarize_workflow_for_meta_answer
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import (
    do_answer_meta_question,
    do_detect_meta_question,
)
from swiss_ai_hub.agent.workflow.decorators.step import step


class LLMWrappingAgent(Agent):
    """A simple agent that wraps an LLM and streams responses to user messages."""

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.llm_wrapping_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:message"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.description"),
        icon="mdi:help-circle-outline",
    )
    async def detect_meta_question_step(
        self,
        event: UserMessageEvent,
        agent_config: LLMWrappingAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        """Gate every chat message: classify it as a meta question or release the normal pipeline."""
        # TEMP: meta-question detection disabled pending investigation. The if/else below always routes
        # to the normal pipeline (still emits the NotAMetaQuestionEvent gate token, so downstream
        # gating/preconditions are unaffected). Flip META_QUESTION_DETECTION_ENABLED to re-enable.
        META_QUESTION_DETECTION_ENABLED = False
        if not META_QUESTION_DETECTION_ENABLED:
            return NotAMetaQuestionEvent(reasoning="meta-question detection temporarily disabled")
        return await do_detect_meta_question(
            user_query=event.user_query,
            llm_config=agent_config.llm,
            displayer=displayer,
            t=t,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.description"),
        icon="mdi:account-voice",
    )
    async def answer_meta_question_step(
        self,
        event: MetaQuestionDetectedEvent,
        user_message_event: UserMessageEvent,
        agent_config: LLMWrappingAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        """Answer a meta question from the agent's own identity and workflow, then stop the run."""
        return await do_answer_meta_question(
            event=event,
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
            workflow_summary=summarize_workflow_for_meta_answer(type(self), t),
            chat_history=user_message_event.messages,
            llm_config=agent_config.llm,
            displayer=displayer,
            t=t,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.limit_chat_history.name"),
        description=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.limit_chat_history.description"),
        icon="mage:edit",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: LLMWrappingAgentConfig,
        _clear: NotAMetaQuestionEvent,
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
        t: LocaleHandler,
        thread_context: ThreadContext,
    ) -> LLMStopEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            stop_event = await displayer.display_llm_stream(
                agent_config.llm, llm, event.limited_history, as_stop_step=True
            )

        # Inline, not a @step: the dispatcher won't dispatch steps waiting on a stop event. See ADR 2026_06_18.
        await generate_conversation_metadata(stop_event.chat_messages, agent_config.llm, displayer, t, thread_context)
        return stop_event
