from typing import Annotated

from aihub_lib.infrastructure.mem0.types.Memory import Memory
from pydantic import BaseModel, Field


class MemoryDTO(BaseModel):
    """Data Transfer Object for a single memory item."""

    id: Annotated[str, Field(description="The unique identifier of the memory.")]
    memory: Annotated[str, Field(description="The memory content deduced from the text data.")]
    score: Annotated[
        float | None,
        Field(description="The relevance score of the memory (present for search results, null otherwise)."),
    ] = None
    created_at: Annotated[str, Field(description="ISO timestamp when the memory was created.")]
    user_id: Annotated[str | None, Field(description="The unique identifier of the user who owns this memory.")] = None
    agent_id: Annotated[
        str | None, Field(description="The unique identifier of the agent that created this memory.")
    ] = None
    thread_id: Annotated[
        str | None, Field(description="The unique identifier of the thread in which this memory was created.")
    ] = None
    display_id: Annotated[
        str | None, Field(description="The unique identifier of the display in which this memory was created..")
    ] = None
    run_id: Annotated[
        str | None, Field(description="The unique identifier of the run in which this memory was created.")
    ] = None

    @classmethod
    def from_memory(cls, memory: Memory) -> "MemoryDTO":
        """Creates a MemoryDTO from a Memory model."""
        return cls(
            id=memory.id,
            memory=memory.memory,
            score=memory.score,
            created_at=memory.created_at,
            user_id=memory.owner_id,
            agent_id=memory.metadata.agent_id,
            thread_id=memory.metadata.thread_id,
            display_id=memory.metadata.display_id,
            run_id=memory.metadata.run_id,
        )
