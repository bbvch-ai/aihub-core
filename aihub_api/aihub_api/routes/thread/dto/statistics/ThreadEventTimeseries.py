from datetime import datetime
from typing import Annotated, List, Literal

from aihub_lib.persistence.messaging.entities.types.EventBucket import EventBucket
from pydantic import BaseModel, Field


class ThreadEventTimeseries(BaseModel):
    """Timeseries of events for a given thread and time-range."""

    thread_id: Annotated[str, Field(description="The thread ID")]
    time_range: Annotated[Literal["1h", "24h", "30d", "365d"], Field(description="Time range for the statistics")]
    resolution: Annotated[Literal["1m", "1h", "1d", "1w"], Field(description="Resolution of the buckets")]
    start_time: Annotated[datetime, Field(description="Start time of the entire range")]
    end_time: Annotated[datetime, Field(description="End time of the entire range")]
    buckets: Annotated[List[EventBucket], Field(description="List of time buckets with event counts")]
