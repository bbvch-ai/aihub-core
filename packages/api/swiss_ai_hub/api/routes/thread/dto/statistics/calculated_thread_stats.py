from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class CalculatedThreadStats(BaseModel):
    """Holds the calculated overall statistics for a thread."""

    num_events: Annotated[int, Field(..., description="Number of events emitted in this thread")] = 0
    num_turns: Annotated[int, Field(..., description="Number of conversation turns in this thread")] = 0
    has_pending: Annotated[bool, Field(..., description="Indicates if the thread has pending operations")] = False
    has_errors: Annotated[bool, Field(..., description="Indicates if the thread has encountered errors")] = False
    is_hitl: Annotated[bool, Field(..., description="Indicates if Human-In-The-Loop is enabled for this thread")] = (
        False
    )
    open_hitl: Annotated[bool, Field(..., description="Indicates if there is an open Human-In-The-Loop request")] = (
        False
    )
    is_bitl: Annotated[bool, Field(..., description="Indicates if Bot-In-The-Loop is enabled for this thread")] = False
    open_bitl: Annotated[bool, Field(..., description="Indicates if there is an open Bot-In-The-Loop request")] = False
    is_aitl: Annotated[bool, Field(..., description="Indicates if AI-In-The-Loop is enabled for this thread")] = False
    open_aitl: Annotated[bool, Field(..., description="Indicates if there is an open AI-In-The-Loop request")] = False
    llm_cost: Annotated[float, Field(..., description="Total cost incurred by LLM operations in this thread")] = 0.0
    first_interaction_dt: Annotated[
        datetime | None, Field(None, description="Timestamp of the first interaction in this thread")
    ] = None
    latest_interaction_dt: Annotated[
        datetime | None, Field(None, description="Timestamp of the most recent interaction in this thread")
    ] = None
    duration: Annotated[float | None, Field(None, description="Response duration in seconds")] = None

    @property
    def first_interaction(self) -> str | None:
        return self.first_interaction_dt.isoformat().replace("+00:00", "Z") if self.first_interaction_dt else None

    @property
    def latest_interaction(self) -> str | None:
        return self.latest_interaction_dt.isoformat().replace("+00:00", "Z") if self.latest_interaction_dt else None
