from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMStopEvent, UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import PresidioAnalyzerClient

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.anonymiser_agent.anonymiser_turn import AnonymiserTurn
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class AnonymiserAgent(Agent):
    """Anonymises a text by hand and restores the answer, so a user can take personal data to any tool safely.

    A single step and no model: the chat content reaches only the deployment's analyzer, which is why it has no
    conversation capability (its title, follow-ups and memory each call a model).
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.anonymiser_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.anonymiser_agent.metadata.description"
    )
    icon: ClassVar[str] = "mdi:incognito"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.anonymiser_agent.steps.respond.name"),
        description=AgentLocaleString.from_i18n_path("agent.anonymiser_agent.steps.respond.description"),
        icon="mdi:incognito",
    )
    async def respond_step(
        self,
        event: UserMessageEvent,
        displayer: EventDisplayer,
        thread_context: ThreadContext,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        return await AnonymiserTurn.answer(event.user_query, PresidioAnalyzerClient(), displayer, thread_context, t)
