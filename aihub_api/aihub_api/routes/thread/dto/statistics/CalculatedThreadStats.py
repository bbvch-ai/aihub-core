from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CalculatedThreadStats(BaseModel):
    """Holds the calculated overall statistics for a thread."""

    num_events: int = 0
    num_turns: int = 0
    has_pending: bool = False
    has_errors: bool = False
    is_hitl: bool = False
    open_hitl: bool = False
    is_bitl: bool = False
    open_bitl: bool = False
    is_aitl: bool = False
    open_aitl: bool = False
    llm_cost: float = 0.0
    first_interaction_dt: Optional[datetime] = None
    latest_interaction_dt: Optional[datetime] = None
    latency: Optional[float] = None

    @property
    def first_interaction(self) -> Optional[str]:
        return self.first_interaction_dt.isoformat().replace("+00:00", "Z") if self.first_interaction_dt else None

    @property
    def latest_interaction(self) -> Optional[str]:
        return self.latest_interaction_dt.isoformat().replace("+00:00", "Z") if self.latest_interaction_dt else None
