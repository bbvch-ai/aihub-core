from typing import Annotated

from pydantic import Field

from aihub_lib.infrastructure.mem0.types.Memory import Memory
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from aihub_lib.infrastructure.mem0.types.MemorySearchResult import MemorySearchResult
from aihub_lib.nats.events import ControlAndDisplayEvent


class RetrieveMemoryEvent(ControlAndDisplayEvent):
    memories: Annotated[list[Memory], Field(description="The list of memories that were retrieved.")] = []
    relations: Annotated[list[MemoryRelation], Field(description="The list of matching memory relations.")]

    @classmethod
    def from_memory_search_result(cls, memory_search_result: MemorySearchResult):
        return cls(memories=memory_search_result.results, relations=memory_search_result.relations)
