from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class EventBucket(BaseModel):
    """Represents a time bucket with event counts by type."""

    start_time: Annotated[datetime, Field(description="Start time of the bucket")]
    end_time: Annotated[datetime, Field(description="End time of the bucket")]
    total_events: Annotated[int, Field(description="Total number of events in this bucket")] = 0
