from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class EventBucket(BaseModel):
    """Represents a time bucket with event counts by type."""

    start_time: Annotated[datetime, Field(description="Start time of the bucket")]
    end_time: Annotated[datetime, Field(description="End time of the bucket")]

    # Event counts by type
    total_events: Annotated[int, Field(description="Total number of events in this bucket")] = 0
    start_events: Annotated[int, Field(description="Number of start events")] = 0
    stop_events: Annotated[int, Field(description="Number of stop events")] = 0
    exception_events: Annotated[int, Field(description="Number of exception events")] = 0
    hitl_events: Annotated[int, Field(description="Number of Human-In-The-Loop events (requests + responses)")] = 0
    bitl_events: Annotated[int, Field(description="Number of Bot-In-The-Loop events (requests + responses)")] = 0
    aitl_events: Annotated[int, Field(description="Number of Agent-In-The-Loop events (requests + responses)")] = 0
    other_events: Annotated[int, Field(description="Number of other events")] = 0