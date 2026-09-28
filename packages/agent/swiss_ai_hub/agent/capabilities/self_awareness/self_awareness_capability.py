from typing import ClassVar

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    LLMStopEvent,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversational_agent_config import ConversationalAgentConfig
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import (
    generate_follow_up_questions,
    generate_title,
)
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.self_awareness.meta_question_workflow_summary import summarize_workflow_for_meta_answer
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import (
    do_answer_meta_question,
    do_detect_meta_question,
)
from swiss_ai_hub.agent.workflow.decorators.step import step


class SelfAwarenessCapability(Capability):
    """
    Meta questions about the blueprint itself ("what can you do?") answered from its identity and workflow
    instead of running the pipeline.

    Detection is the gate the conversational spine waits on: it clears every other chat message with
    `NotAMetaQuestionEvent`, so a blueprint that installs this capability needs no gating of its own.
    """

    required_config: ClassVar[type[ConversationalAgentConfig]] = ConversationalAgentConfig

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.description"),
        icon="mdi:help-circle-outline",
    )
    async def detect_meta_question_step(
        agent: Agent,
        event: UserMessageEvent,
        agent_config: ConversationalAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        """Gate every chat message: classify it as a meta question or release the normal pipeline."""
        return await do_detect_meta_question(
            user_query=event.user_query,
            llm_config=agent_config.task_llm,
            displayer=displayer,
            user=user,
            t=t,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.description"),
        icon="mdi:account-voice",
    )
    async def answer_meta_question_step(
        agent: Agent,
        event: MetaQuestionDetectedEvent,
        user_message_event: UserMessageEvent,
        agent_config: ConversationalAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> LLMStopEvent:
        """Answer a meta question from the blueprint's own identity and workflow, then stop the run.

        Follow-ups only: the title runs in parallel via `generate_meta_question_title_step`, since it needs
        the topic, not the answer.
        """
        stop_event = await do_answer_meta_question(
            event=event,
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
            workflow_summary=summarize_workflow_for_meta_answer(type(agent), t),
            chat_history=user_message_event.messages,
            llm_config=agent_config.task_llm,
            displayer=displayer,
            user=user,
            t=t,
        )
        await generate_follow_up_questions(stop_event.chat_messages, agent_config.task_llm, displayer, t, user)
        return stop_event

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.description"),
        icon="mdi:format-title",
        stop_on_error=False,
    )
    async def generate_meta_question_title_step(
        agent: Agent,
        event: MetaQuestionDetectedEvent,
        user_message_event: UserMessageEvent,
        agent_config: ConversationalAgentConfig,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> None:
        """Generate the thread's title in parallel with the meta answer, which it must not wait for."""
        await generate_title(
            chat_messages=user_message_event.messages,
            llm_config=agent_config.task_llm,
            displayer=displayer,
            t=t,
            thread_context=thread_context,
            user=user,
        )
