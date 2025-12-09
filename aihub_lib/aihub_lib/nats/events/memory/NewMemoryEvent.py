from typing import Annotated

from pydantic import Field

from aihub_lib.infrastructure.mem0.types.MemoryAdded import MemoryAdded
from aihub_lib.infrastructure.mem0.types.MemoryEventType import MemoryEventType
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class NewMemoryEvent(ControlAndDisplayEvent):
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
