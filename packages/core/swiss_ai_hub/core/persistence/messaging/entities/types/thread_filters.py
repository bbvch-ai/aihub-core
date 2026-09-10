from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class ThreadFilters(BaseModel):
    """Resolved, entity-ready filters for thread list queries."""

    search: Annotated[str | None, Field(description="Search with thread name")] = None
    agent_id: Annotated[str | None, Field(description="Only threads that include this agent instance id")] = None
    user_search_id: Annotated[str | None, Field(description="Only threads that also include this user id")] = None
    status_thread_ids: Annotated[list[str] | None, Field(description="Filter with status thread ids")] = None
    from_date: Annotated[datetime | None, Field(description="Only threads created on or after this date")] = None
    to_date: Annotated[datetime | None, Field(description="Only threads created on or before this date")] = None
