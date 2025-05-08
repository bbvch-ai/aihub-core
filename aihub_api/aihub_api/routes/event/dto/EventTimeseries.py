from datetime import datetime
from typing import Annotated, List, Optional

from aihub_lib.persistence.messaging.entities.PersistedEventEntity import (
    EVENT_TIMESERIES_RESOLUTION,
    EVENT_TIMESERIES_TIME_RANGE,
)
from aihub_lib.persistence.messaging.entities.types.EventBucket import EventBucket
from pydantic import BaseModel, Field


class EventTimeseries(BaseModel):
    """Timeseries of events for a given thread and time-range."""

    thread_id: Annotated[Optional[str], Field(description="The thread ID to filter for")]
    agent_id: Annotated[Optional[str], Field(description="The Agent ID to filter for")]
    agent_class: Annotated[Optional[str], Field(description="The Agent Class to filter for")]
    event_name: Annotated[Optional[str], Field(description="Event Name to filter for")]

    time_range: Annotated[EVENT_TIMESERIES_TIME_RANGE, Field(description="Time range for the statistics")]
    resolution: Annotated[EVENT_TIMESERIES_RESOLUTION, Field(description="Resolution of the buckets")]
    start_time: Annotated[datetime, Field(description="Start time of the entire range")]
    end_time: Annotated[datetime, Field(description="End time of the entire range")]
    buckets: Annotated[List[EventBucket], Field(description="List of time buckets with event counts")]
