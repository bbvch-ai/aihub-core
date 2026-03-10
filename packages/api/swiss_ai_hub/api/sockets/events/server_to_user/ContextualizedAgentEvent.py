import json
from typing import Annotated, Any, Self, override

from pydantic import BaseModel, Discriminator, Field, Tag
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.nats.events.agent_in_the_loop.exception.AgentInTheLoopExceptionEvent import (
    AgentInTheLoopExceptionEvent,
)
from swiss_ai_hub.core.nats.events.agent_in_the_loop.request.AgentInTheLoopRequestEvent import (
    AgentInTheLoopRequestEvent,
)
from swiss_ai_hub.core.nats.events.agent_in_the_loop.response.AgentInTheLoopResponseEvent import (
    AgentInTheLoopResponseEvent,
)
from swiss_ai_hub.core.nats.events.common.LimitChatHistoryEvent import LimitChatHistoryEvent
from swiss_ai_hub.core.nats.events.common.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from swiss_ai_hub.core.nats.events.control.exception.ExceptionEvent import ExceptionEvent
from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent
from swiss_ai_hub.core.nats.events.control.stop.StopEvent import StopEvent
from swiss_ai_hub.core.nats.events.cost.LLMCostEvent import LLMCostEvent
from swiss_ai_hub.core.nats.events.display.ChunkEvent import ChunkEvent
from swiss_ai_hub.core.nats.events.display.DisplayEvent import DisplayEvent
from swiss_ai_hub.core.nats.events.display.ThoughtEvent import ThoughtEvent
from swiss_ai_hub.core.nats.events.guard.AgentSuitabilityAcceptEvent import AgentSuitabilityAcceptEvent
from swiss_ai_hub.core.nats.events.guard.AgentSuitabilityRejectEvent import AgentSuitabilityRejectEvent
from swiss_ai_hub.core.nats.events.guard.ContextInsufficientRejectEvent import ContextInsufficientRejectEvent
from swiss_ai_hub.core.nats.events.guard.ContextSufficientAcceptEvent import ContextSufficientAcceptEvent
from swiss_ai_hub.core.nats.events.guard.FewShotAcceptEvent import FewShotAcceptEvent
from swiss_ai_hub.core.nats.events.guard.FewShotRejectEvent import FewShotRejectEvent
from swiss_ai_hub.core.nats.events.guard.GuardAcceptEvent import GuardAcceptEvent
from swiss_ai_hub.core.nats.events.guard.GuardRejectionEvent import GuardRejectionEvent
from swiss_ai_hub.core.nats.events.guard.SensitiveInfoAcceptEvent import SensitiveInfoAcceptEvent
from swiss_ai_hub.core.nats.events.guard.SensitiveInfoRejectEvent import SensitiveInfoRejectEvent
from swiss_ai_hub.core.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopResponseEvent,
)
from swiss_ai_hub.core.nats.events.memory.history.AddMemoryToChatHistoryEvent import AddMemoryToChatHistoryEvent
from swiss_ai_hub.core.nats.events.memory.history.AddOrganizationMemoryToChatHistoryEvent import (
    AddOrganizationMemoryToChatHistoryEvent,
)
from swiss_ai_hub.core.nats.events.memory.history.AddUserMemoryToChatHistoryEvent import AddUserMemoryToChatHistoryEvent
from swiss_ai_hub.core.nats.events.memory.retrieve.BaseRetrieveMemoryEvent import BaseRetrieveMemoryEvent
from swiss_ai_hub.core.nats.events.memory.retrieve.RetrieveOrganizationMemoryEvent import (
    RetrieveOrganizationMemoryEvent,
)
from swiss_ai_hub.core.nats.events.memory.retrieve.RetrieveUserMemoryEvent import RetrieveUserMemoryEvent
from swiss_ai_hub.core.nats.events.memory.store.BaseStoreMemoryEvent import BaseStoreMemoryEvent
from swiss_ai_hub.core.nats.events.memory.store.StoreOrganizationMemoryEvent import StoreOrganizationMemoryEvent
from swiss_ai_hub.core.nats.events.memory.store.StoreUserMemoryEvent import StoreUserMemoryEvent
from swiss_ai_hub.core.nats.events.router.RouterEvent import RouterEvent
from swiss_ai_hub.core.nats.events.semantic.agent.AgentEvent import AgentEvent
from swiss_ai_hub.core.nats.events.semantic.chain.ChainEvent import ChainEvent
from swiss_ai_hub.core.nats.events.semantic.embedding.EmbeddingEvent import EmbeddingEvent
from swiss_ai_hub.core.nats.events.semantic.guard.GuardEvent import GuardEvent
from swiss_ai_hub.core.nats.events.semantic.llm.LLMEvent import LLMEvent
from swiss_ai_hub.core.nats.events.semantic.llm.LLMStopEvent import LLMStopEvent
from swiss_ai_hub.core.nats.events.semantic.reranker.RerankerEvent import RerankerEvent
from swiss_ai_hub.core.nats.events.semantic.retriever.RetrieverEvent import RetrieverEvent
from swiss_ai_hub.core.nats.events.semantic.SemanticEvent import SemanticEvent
from swiss_ai_hub.core.nats.events.semantic.tool.ToolEvent import ToolEvent
from swiss_ai_hub.core.nats.events.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.persistence.messaging.entities.PersistedAgentEventEntity import PersistedAgentEventEntity

# Import all events here that the frontend should be able to display
DisplayEvents = (
    Annotated[StartEvent, Tag("StartEvent")]
    | Annotated[AgentInTheLoopResponseEvent, Tag("AgentInTheLoopResponseEvent")]
    | Annotated[HumanInTheLoopRequestEvent, Tag("HumanInTheLoopRequestEvent")]
    | Annotated[AgentInTheLoopRequestEvent, Tag("AgentInTheLoopRequestEvent")]
    | Annotated[AgentInTheLoopExceptionEvent, Tag("AgentInTheLoopExceptionEvent")]
    | Annotated[HumanInTheLoopResponseEvent, Tag("HumanInTheLoopResponseEvent")]
    | Annotated[LimitChatHistoryEvent, Tag("LimitChatHistoryEvent")]
    | Annotated[AddMemoryToChatHistoryEvent, Tag("AddMemoryToChatHistoryEvent")]
    | Annotated[AddUserMemoryToChatHistoryEvent, Tag("AddUserMemoryToChatHistoryEvent")]
    | Annotated[AddOrganizationMemoryToChatHistoryEvent, Tag("AddOrganizationMemoryToChatHistoryEvent")]
    | Annotated[StandaloneQuestionCondenserEvent, Tag("StandaloneQuestionCondenserEvent")]
    | Annotated[LLMCostEvent, Tag("LLMCostEvent")]
    | Annotated[ChunkEvent, Tag("ChunkEvent")]
    | Annotated[ThoughtEvent, Tag("ThoughtEvent")]
    | Annotated[GuardEvent, Tag("GuardEvent")]
    | Annotated[RouterEvent, Tag("RouterEvent")]
    | Annotated[GuardRejectionEvent, Tag("GuardRejectionEvent")]
    | Annotated[SemanticEvent, Tag("SemanticEvent")]
    | Annotated[AgentEvent, Tag("AgentEvent")]
    | Annotated[ChainEvent, Tag("ChainEvent")]
    | Annotated[EmbeddingEvent, Tag("EmbeddingEvent")]
    | Annotated[LLMEvent, Tag("LLMEvent")]
    | Annotated[LLMStopEvent, Tag("LLMStopEvent")]
    | Annotated[RerankerEvent, Tag("RerankerEvent")]
    | Annotated[RetrieverEvent, Tag("RetrieverEvent")]
    | Annotated[ToolEvent, Tag("ToolEvent")]
    | Annotated[UserMessageEvent, Tag("UserMessageEvent")]
    | Annotated[ExceptionEvent, Tag("ExceptionEvent")]
    | Annotated[StopEvent, Tag("StopEvent")]
    | Annotated[DisplayEvent, Tag("DisplayEvent")]
    | Annotated[GuardAcceptEvent, Tag("GuardAcceptEvent")]
    | Annotated[AgentSuitabilityAcceptEvent, Tag("AgentSuitabilityAcceptEvent")]
    | Annotated[AgentSuitabilityRejectEvent, Tag("AgentSuitabilityRejectEvent")]
    | Annotated[ContextSufficientAcceptEvent, Tag("ContextSufficientAcceptEvent")]
    | Annotated[ContextInsufficientRejectEvent, Tag("ContextInsufficientRejectEvent")]
    | Annotated[FewShotAcceptEvent, Tag("FewShotAcceptEvent")]
    | Annotated[FewShotRejectEvent, Tag("FewShotRejectEvent")]
    | Annotated[SensitiveInfoAcceptEvent, Tag("SensitiveInfoAcceptEvent")]
    | Annotated[SensitiveInfoRejectEvent, Tag("SensitiveInfoRejectEvent")]
    | Annotated[StoreUserMemoryEvent, Tag("StoreUserMemoryEvent")]
    | Annotated[BaseRetrieveMemoryEvent, Tag("BaseRetrieveMemoryEvent")]
    | Annotated[BaseStoreMemoryEvent, Tag("BaseStoreMemoryEvent")]
    | Annotated[RetrieveOrganizationMemoryEvent, Tag("RetrieveOrganizationMemoryEvent")]
    | Annotated[RetrieveUserMemoryEvent, Tag("RetrieveUserMemoryEvent")]
    | Annotated[StoreOrganizationMemoryEvent, Tag("StoreOrganizationMemoryEvent")]
)


def event_discriminator(event: DisplayEvent) -> str:
    valid_tags = [arg.__metadata__[0].tag for arg in DisplayEvents.__args__]

    # Return "DisplayEvent" if _event_name is missing or not in valid_tags
    if not hasattr(event, "_event_name"):
        return "DisplayEvent"

    if event._event_name in valid_tags:
        return event._event_name

    for event_name in event._parent_event_names:
        if event_name in valid_tags:
            return event_name

    return "DisplayEvent"


class ContextualizedAgentEvent(BaseModel):
    """
    Wraps an agent event with context information like the agent's class, ID, and thread ID.
    This is necessary as the event payload itself is independent of the topic context through
    which the event was published.
    This class ensures that both the information from the topic context and the event itself is bundled
    together.
    """

    locale: Annotated[
        str,
        Field(
            description="The locale in which event name and description is returned.",
        ),
    ] = LocaleHandler.DEFAULT_LOCALE
    event_display_name: Annotated[str, Field(description="Display name for the event")]
    event_display_description: Annotated[str, Field(description="Display description for the event")]

    agent_class: Annotated[str, Field(description="The agent class responsible for this event.")]
    agent_id: Annotated[str, Field(description="Unique identifier of the agent instance that produced the event.")]
    thread_id: Annotated[
        str, Field(description="Thread identifier linking events to a particular conversation or workflow.")
    ]
    display_id: Annotated[str, Field(description="Display session ID, used to group events for the UI.")]
    run_id: Annotated[str, Field(description="Optional run ID if the event is associated with a particular run.")]
    event_type: Annotated[str, Field(description="Type of the event (default: 'display_event').")]
    event_name: Annotated[str, Field(description="Name of the event, indicating its subtype or category.")]
    event_id: Annotated[str, Field(description="Unique identifier of this event instance.")]
    event: Annotated[
        DisplayEvents,
        Field(
            description="Data of the event itself.",
            discriminator=Discriminator(event_discriminator),
        ),
    ]

    @classmethod
    def from_persisted_event(cls, persisted_event: PersistedAgentEventEntity, locale: str | None = None) -> Self:
        """
        Construct a ContextualizedAgentEvent from a PersistedAgentEventEntity, converting persisted event data
        into a client-ready format.
        """
        locale_handler = LocaleHandler(locale=locale)
        display_event = DisplayEvent.deserialize_event(persisted_event.event_data)
        return cls(
            locale=locale or locale_handler.DEFAULT_LOCALE,
            agent_class=persisted_event.agent_class,
            agent_id=persisted_event.agent_id,
            thread_id=persisted_event.thread_id,
            display_id=persisted_event.display_id,
            run_id=persisted_event.run_id,
            event_type=persisted_event.event_type,
            event_name=persisted_event.event_name,
            event_id=persisted_event.event_id,
            event=display_event,
            event_display_name=locale_handler.extract(display_event.display_name),
            event_display_description=locale_handler.extract(display_event.display_description),
        )

    @override
    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        Serializes the event into a dictionary. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        data = super().model_dump(**kwargs)
        return {**data, "event": self.event.model_dump(**kwargs)}

    @override
    def model_dump_json(self, **kwargs: Any) -> str:
        """
        Serializes the event into a JSON string. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        return json.dumps(self.model_dump(**kwargs), default=str)
