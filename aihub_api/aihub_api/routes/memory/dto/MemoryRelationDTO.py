from typing import Annotated

from aihub_lib.infrastructure.mem0.types.MemoryRelation import MemoryRelation
from pydantic import BaseModel, Field


class MemoryRelationDTO(BaseModel):
    """Data Transfer Object for a knowledge graph relation (triple)."""

    source: Annotated[str, Field(description="The source entity in the knowledge graph.")]
    relation: Annotated[str, Field(description="The relationship type between source and target entities.")]
    target: Annotated[str, Field(description="The target entity in the knowledge graph.")]

    @classmethod
    def from_relation(cls, relation: MemoryRelation) -> "MemoryRelationDTO":
        """Creates a MemoryRelationDTO from a MemoryRelation model."""
        return cls(
            source=relation.source,
            relation=relation.relation,
            target=relation.target,
        )
