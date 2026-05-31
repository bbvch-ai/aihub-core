from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMStopEvent, MetaQuestionDetectedEvent, NotAMetaQuestionEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.workflow import DispatchableWorkflow

from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import (
    do_answer_meta_question,
    do_detect_meta_question,
)


class SelfAwarenessMixin:
    """
    Gives a conversational agent built-in answers to meta questions about itself
    ("what can you do?", "why did you do X?").

    Adopting an agent: inherit this alongside `Agent`, implement `self_awareness_llm_config`,
    and add two thin `@step` methods that delegate to `run_meta_question_detection` and
    `run_meta_question_answer`. The steps cannot live here because the dispatcher injects
    the concrete `AgentConfig` subclass by exact type — a base-class annotation is rejected.
    """

    SELF_AWARENESS_STEP_NAMES: frozenset[str] = frozenset({"detect_meta_question_step", "answer_meta_question_step"})

    def self_awareness_llm_config(self, agent_config: AgentConfig) -> LLMConfig:
        """Return the LLM the agent uses to classify and answer meta questions."""
        raise NotImplementedError(
            f"{type(self).__name__} uses SelfAwarenessMixin but does not implement self_awareness_llm_config()."
        )

    def meta_question_workflow_summary(self, t: LocaleHandler) -> str:
        """A human-readable list of the agent's own workflow steps, used to ground meta answers."""
        lines: list[str] = []
        for step in self.get_steps():
            if step.__name__ in self.SELF_AWARENESS_STEP_NAMES:
                continue
            name = getattr(step, DispatchableWorkflow.STEP_NAME_ANNOTATION, None)
            if name is None:
                continue
            description = getattr(step, DispatchableWorkflow.STEP_DESCRIPTION_ANNOTATION, None)
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
