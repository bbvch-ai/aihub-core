from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation


class ModifiedRelations(BaseModel):
    deleted_entities: Annotated[list[MemoryRelation], Field(description="The list of deleted entities.")] = []
    added_entities: Annotated[list[MemoryRelation], Field(description="The list of added entities.")] = []
