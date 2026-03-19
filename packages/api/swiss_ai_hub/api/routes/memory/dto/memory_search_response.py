from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.memory.dto.memory_dto import MemoryDTO
from swiss_ai_hub.api.routes.memory.dto.memory_relation_dto import MemoryRelationDTO


class MemorySearchResponse(BaseModel):
    """Response for searching memories with scored results and matching graph relations."""

    query: Annotated[str, Field(description="The original search query used.")]
    total: Annotated[int, Field(description="Total number of search results matching the query.")]
    memories: Annotated[
        list[MemoryDTO],
        Field(
            description="List of memories matching the search query, ordered by relevance score. "
            "Each memory includes a score field indicating relevance to the query."
        ),
    ]
    relations: Annotated[
        list[MemoryRelationDTO],
        Field(
            description="Knowledge graph relations involving entities from the search results. "
            "Used for highlighting matching triples in the graph visualization. "
            "Only includes relations where both source AND target appear in the search results."
        ),
    ]
