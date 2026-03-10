from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.memory.dto.MemoryDTO import MemoryDTO
from swiss_ai_hub.api.routes.memory.dto.MemoryRelationDTO import MemoryRelationDTO


class MemoriesResponse(BaseModel):
    """Response for listing user memories with full knowledge graph."""

    total: Annotated[
        int,
        Field(
            description="Total number of memories returned. Respects limit and filters. "
            "Does not include graph relation count."
        ),
    ]
    memories: Annotated[
        list[MemoryDTO],
        Field(description="List of memory items. Limited by the 'limit' query parameter and filtered by user/agent."),
    ]
    relations: Annotated[
        list[MemoryRelationDTO],
        Field(
            description="FULL knowledge graph relations for the user. "
            "Includes all graph triples regardless of limit/filters for complete graph visualization."
        ),
    ]
