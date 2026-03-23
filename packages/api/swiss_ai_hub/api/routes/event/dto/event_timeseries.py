from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import Resolution, TimeRange
from swiss_ai_hub.core.persistence.messaging.entities.types.event_bucket import EventBucket


class EventTimeseries(BaseModel):
    """Timeseries of events for a given time-range."""

    thread_id: Annotated[str | None, Field(description="The thread ID to filter for")]
    agent_id: Annotated[str | None, Field(description="The Agent ID to filter for")]
    agent_class: Annotated[str | None, Field(description="The Agent Class to filter for")]
    event_name: Annotated[str | None, Field(description="Event Name to filter for")]

    time_range: Annotated[TimeRange, Field(description="Time range for the statistics")]
    resolution: Annotated[Resolution, Field(description="Resolution of the buckets")]
    start_time: Annotated[datetime, Field(description="Start time of the entire range")]
    end_time: Annotated[datetime, Field(description="End time of the entire range")]
    buckets: Annotated[list[EventBucket], Field(description="List of time buckets with event counts")]
