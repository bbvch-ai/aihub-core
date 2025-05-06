from datetime import datetime
from typing import Annotated, Dict, List, Literal, Optional

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


class ThreadTimeStatisticsDTO(BaseModel):
    """Statistics for a thread over a specific time range with bucketed data."""

    thread_id: Annotated[str, Field(description="The thread ID")]
    time_range: Annotated[Literal["1h", "24h", "30d", "365d"], Field(description="Time range for the statistics")]
    resolution: Annotated[Literal["1m", "1h", "1d", "1w"], Field(description="Resolution of the buckets")]
    start_time: Annotated[datetime, Field(description="Start time of the entire range")]
    end_time: Annotated[datetime, Field(description="End time of the entire range")]
    buckets: Annotated[List[EventBucket], Field(description="List of time buckets with event counts")]
