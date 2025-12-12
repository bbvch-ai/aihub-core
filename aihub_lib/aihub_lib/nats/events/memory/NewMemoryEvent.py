from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mem0.types.MemoryAdded import MemoryAdded
from aihub_lib.infrastructure.mem0.types.MemoryEventType import MemoryEventType
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class NewMemoryEvent(ControlAndDisplayEvent):
    """
    A control and display event emitted when an agent updates user or organization memories.

    ### Why NewMemoryEvent?
    This event serves dual purposes in the Swiss AI Agent Protocol:
    - As a control event, it notifies downstream systems that memory state has changed
    - As a display event, it provides transparency to users about what was learned from their conversation

    Agents use this event after processing conversation context to persist insights. The event captures
    both the semantic changes (added/updated/deleted memories) and the knowledge graph updates
    (new/removed relations between entities). This enables:
    - Real-time UI updates showing memory modifications
    - Audit trails of what agents learned and when
    - Triggering downstream workflows that depend on memory state
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.new_memory_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.new_memory_event.description"
    )
    added_memories: Annotated[list[str], Field(description="Newly added memory texts")]
    updated_memories: Annotated[list[str], Field(description="Updated memory texts")]
    deleted_memories: Annotated[list[str], Field(description="Deleted memory texts")]

    added_relations: Annotated[list[MemoryRelation], Field(description="Newly added relations")]
    deleted_relations: Annotated[list[MemoryRelation], Field(description="Deleted relations")]

    @classmethod
    def from_memory_added_object(cls, memory_added: MemoryAdded):
        return cls(
            added_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.ADD],
            updated_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.UPDATE],
            deleted_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.DELETE],
            added_relations=memory_added.relations.added_entities,
            deleted_relations=memory_added.relations.deleted_entities,
        )
