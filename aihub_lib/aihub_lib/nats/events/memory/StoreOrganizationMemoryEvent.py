from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mem0.types.MemoryAdded import MemoryAdded
from aihub_lib.infrastructure.mem0.types.MemoryEventType import MemoryEventType
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class StoreOrganizationMemoryEvent(ControlAndDisplayEvent):
    """
    A control and display event emitted when an agent stores an explicit organization memory.

    ### Why StoreOrganizationMemoryEvent?
    This event serves dual purposes in the Swiss AI Agent Protocol:
    - As a control event, it passes the stored organization memory to downstream workflow steps
    - As a display event, it provides transparency to users about what organizational fact was persisted

    Unlike user memories (which are inferred from chat history), organization memories are explicit
    facts provided by users. This event confirms successful storage and makes the operation auditable.

    Organization memories are shared across all users within the organization namespace, making
    this event critical for tracking what shared knowledge has been added to the organization's
    knowledge base.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.store_organization_memory_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.store_organization_memory_event.description"
    )

    added_memories: Annotated[list[str], Field(description="Newly added organization memory texts")]
    updated_memories: Annotated[list[str], Field(description="Updated organization memory texts")]
    deleted_memories: Annotated[list[str], Field(description="Deleted organization memory texts")]

    added_relations: Annotated[list[MemoryRelation], Field(description="Newly added relations")]
    deleted_relations: Annotated[list[MemoryRelation], Field(description="Deleted relations")]

    @classmethod
    def from_memory_added_object(cls, memory_added: MemoryAdded) -> "StoreOrganizationMemoryEvent":
        """Create event from mem0's MemoryAdded response object."""
        return cls(
            added_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.ADD],
            updated_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.UPDATE],
            deleted_memories=[m.memory for m in memory_added.results if m.event == MemoryEventType.DELETE],
            added_relations=memory_added.relations.added_entities,
            deleted_relations=memory_added.relations.deleted_entities,
        )
