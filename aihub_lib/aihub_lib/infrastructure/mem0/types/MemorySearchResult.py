from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.infrastructure.mem0.types.Memory import Memory
from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation


class MemorySearchResult(BaseModel):
    results: Annotated[list[Memory], Field(description="The list of matching memories.")]
    relations: Annotated[list[MemoryRelation], Field(description="The list of matching memory relations.")]
