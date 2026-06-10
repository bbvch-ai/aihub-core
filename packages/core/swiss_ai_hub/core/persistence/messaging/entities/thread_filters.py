from datetime import datetime

from pydantic import BaseModel


class ThreadFilters(BaseModel):
    """Resolved, entity-ready filters for thread list queries."""

    search: str | None = None
    agent_id: str | None = None
    user_search_id: str | None = None
    status_thread_ids: list[str] | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
