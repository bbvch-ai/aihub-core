from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_relation import MemoryRelation


class MemorySearchResult(BaseModel):
    results: Annotated[list[Memory], Field(description="The list of matching memories.")]
    # Defaults to empty: when the graph store is disabled (e.g. user memory), mem0 omits the `relations` key.
    relations: Annotated[
        list[MemoryRelation], Field(default_factory=list, description="The list of matching memory relations.")
    ]
