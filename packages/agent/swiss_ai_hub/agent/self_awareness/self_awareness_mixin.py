from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    LLMStopEvent,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.workflow import DispatchableWorkflow

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import (
    do_answer_meta_question,
    do_detect_meta_question,
)
from swiss_ai_hub.agent.workflow.decorators.step import step


class SelfAwarenessMixin:
    """
    Gives a conversational agent built-in answers to meta questions about itself
    ("what can you do?", "why did you do X?").

    `Agent` inherits this mixin, so the two self-awareness `@step` methods are available to every
    agent blueprint. They are kept dormant — filtered out of `Agent.get_steps()` — until a subclass
    opts in by overriding `self_awareness_llm_config` (see `Agent._is_self_aware`). An opting-in
    agent must additionally gate its raw `UserMessageEvent` entry steps with
    `check_passed_meta_question_gate`; the gating cannot be automated because each agent has different
    entry steps. The base-class steps are annotated with the base `AgentConfig`; the dispatcher injects
    the run's concrete config because its check is subclass-based.
    """

    SELF_AWARENESS_STEP_NAMES: frozenset[str] = frozenset({"detect_meta_question_step", "answer_meta_question_step"})

    def self_awareness_llm_config(self, agent_config: AgentConfig) -> LLMConfig:
        """
        Return the LLM the agent uses to classify and answer meta questions.

        Overriding this is the opt-in signal: an agent that overrides it becomes "self-aware" and the
        detection/answer steps are activated for it.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement self_awareness_llm_config(); self-awareness is disabled."
        )

    def meta_question_workflow_summary(self, t: LocaleHandler) -> str:
        """A human-readable list of the agent's own workflow steps, used to ground meta answers."""
        lines: list[str] = []
        for workflow_step in self.get_steps():
            if workflow_step.__name__ in self.SELF_AWARENESS_STEP_NAMES:
                continue
            name = getattr(workflow_step, DispatchableWorkflow.STEP_NAME_ANNOTATION, None)
            if name is None:
                continue
            description = getattr(workflow_step, DispatchableWorkflow.STEP_DESCRIPTION_ANNOTATION, None)
            detail = f": {t.extract(description)}" if description is not None else ""
            lines.append(f"- {t.extract(name)}{detail}")
        return "\n".join(lines)

    async def run_meta_question_detection(
        self,
        user_query: str,
        agent_config: AgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        return await do_detect_meta_question(
            user_query=user_query,
            llm_config=self.self_awareness_llm_config(agent_config),
            displayer=displayer,
            t=t,
        )

    async def run_meta_question_answer(
        self,
        event: MetaQuestionDetectedEvent,
        chat_history: list[ChatMessage],
        agent_config: AgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        return await do_answer_meta_question(
            event=event,
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
            workflow_summary=self.meta_question_workflow_summary(t),
            chat_history=chat_history,
            llm_config=self.self_awareness_llm_config(agent_config),
            displayer=displayer,
            t=t,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.description"),
        icon="mdi:help-circle-outline",
    )
    async def detect_meta_question_step(
        self,
        event: UserMessageEvent,
        agent_config: AgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        """Gate every chat message: classify it as a meta question or release the normal pipeline."""
        return await self.run_meta_question_detection(event.user_query, agent_config, displayer, t)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.description"),
        icon="mdi:account-voice",
    )
    async def answer_meta_question_step(
        self,
        event: MetaQuestionDetectedEvent,
        user_message_event: UserMessageEvent,
        agent_config: AgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        """Answer a meta question from the agent's own identity and workflow, then stop the run."""
        return await self.run_meta_question_answer(event, user_message_event.messages, agent_config, displayer, t)
