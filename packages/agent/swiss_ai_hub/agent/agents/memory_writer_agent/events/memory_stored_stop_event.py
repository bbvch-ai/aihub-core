from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.events.agent import StopEvent, StoreUserMemoryEvent


class MemoryStoredStopEvent(StopEvent):
    """
    Terminal event for the `MemoryWriterAgent`, carrying the memory-write summary.

    Unlike a bare `StopEvent`, this surfaces what was actually persisted (added/updated/deleted memories) in
    the writer run's trace, mirroring the observability of the inline `StoreUserMemoryEvent`. Graph relations
    are not surfaced: user memory runs without the graph store (issue #1179), so they are always empty here.
    """

    added_memories: Annotated[list[str], Field(default_factory=list, description="Newly added memory texts")]
    updated_memories: Annotated[list[str], Field(default_factory=list, description="Updated memory texts")]
    deleted_memories: Annotated[list[str], Field(default_factory=list, description="Deleted memory texts")]

    @classmethod
    def from_store_event(cls, store_event: StoreUserMemoryEvent) -> Self:
        """Build from a `StoreUserMemoryEvent` so the mem0-result mapping stays in one place."""
        return cls(
            added_memories=store_event.added_memories,
            updated_memories=store_event.updated_memories,
            deleted_memories=store_event.deleted_memories,
        )
