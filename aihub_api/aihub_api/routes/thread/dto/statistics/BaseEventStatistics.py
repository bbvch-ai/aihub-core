from typing import Annotated

from pydantic import BaseModel, Field


class BaseEventStatistics(BaseModel):
    """Base class for event statistics with common boolean flags and timing."""

    n_events: Annotated[int, Field(description="Total number of events")] = 0
    has_errors: Annotated[bool, Field(description="Has error events")] = False
    has_pending: Annotated[bool, Field(description="Has pending events (more start than stop/exception events)")] = (
        False
    )
    is_hitl: Annotated[bool, Field(description="Has HITL events")] = False
    open_hitl: Annotated[bool, Field(description="Has open HITL requests")] = False
    is_bitl: Annotated[bool, Field(description="Has BITL events")] = False
    open_bitl: Annotated[bool, Field(description="Has open BITL requests")] = False
    is_aitl: Annotated[bool, Field(description="Has AITL events")] = False
    open_aitl: Annotated[bool, Field(description="Has open AITL requests")] = False
    started_at: Annotated[str | None, Field(description="Start time (ISO format string)")] = None
    ended_at: Annotated[str | None, Field(description="End time (ISO format string)")] = None
    duration: Annotated[float | None, Field(description="Duration in seconds")] = None
