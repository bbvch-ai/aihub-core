from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_relation import MemoryRelation


class MemorySearchResult(BaseModel):
    results: Annotated[list[Memory], Field(description="The list of matching memories.")]
    relations: Annotated[list[MemoryRelation], Field(description="The list of matching memory relations.")]
