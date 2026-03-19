from abc import ABC
from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.infrastructure.mem0.types.memory_added import MemoryAdded
from swiss_ai_hub.core.infrastructure.mem0.types.memory_event_type import MemoryEventType
from swiss_ai_hub.core.infrastructure.mem0.types.memory_relation import MemoryRelation


class BaseStoreMemoryEvent(ControlAndDisplayEvent, ABC):
    """
    Abstract base class for memory storage events.

    ### Why BaseStoreMemoryEvent?
    This event serves dual purposes in the Swiss AI Agent Protocol:
    - As a control event, it notifies downstream systems that memory state has changed
    - As a display event, it provides transparency to users about what was learned or stored

    Agents emit this event after persisting insights to long-term memory storage. The event captures
    both the semantic changes (added/updated/deleted memories) and the knowledge graph updates
    (new/removed relations between entities). This transparency is crucial for user trust - they can
    see what the agent learned and verify accuracy.

    The event structure follows mem0's MemoryAdded response format, enabling real-time UI updates,
    audit trails, and triggering downstream workflows that depend on memory state.

    Concrete subclasses differentiate between user-scoped and organization-scoped memory storage.
    """

    added_memories: Annotated[list[str], Field(description="Newly added memory texts")]
    updated_memories: Annotated[list[str], Field(description="Updated memory texts")]
    deleted_memories: Annotated[list[str], Field(description="Deleted memory texts")]

    added_relations: Annotated[list[MemoryRelation], Field(description="Newly added relations")]
    deleted_relations: Annotated[list[MemoryRelation], Field(description="Deleted relations")]

    @classmethod
    def from_memory_added_object(cls, memory_added: MemoryAdded) -> Self:
        """Create event from mem0's MemoryAdded response object."""
        return cls(
            added_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.ADD],
            updated_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.UPDATE],
            deleted_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.DELETE],
            added_relations=memory_added.relations.added_entities,
            deleted_relations=memory_added.relations.deleted_entities,
        )
