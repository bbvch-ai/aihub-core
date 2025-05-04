from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from aihub_api.routes.thread.dto.statistics.RunStatistics import RunStatistics


class IntermediateDisplayStats(BaseModel):
    """
    Internal model to accumulate stats for a display during processing.
    Uses datetime objects internally. Not intended for direct API response.
    """

    display_id: str
    runs: List[RunStatistics] = []

    # Raw counts
    n_events: int = 0
    start_events: int = 0
    stop_events: int = 0
    exception_events: int = 0
    hitl_request_events: int = 0
    hitl_response_events: int = 0
    bitl_request_events: int = 0
    bitl_response_events: int = 0
    aitl_request_events: int = 0
    aitl_response_events: int = 0
    llm_cost: float = 0.0

    first_event_time: Optional[datetime] = None
    latest_event_time: Optional[datetime] = None

    def update_from_run_data(self, run_data: Dict[str, Any]):
        """Updates counts and times based on raw data dictionary from aggregation."""
        self.n_events += run_data.get("n_events", 0)
        self.start_events += run_data.get("start_events", 0)
        self.stop_events += run_data.get("stop_events", 0)
        self.exception_events += run_data.get("exception_events", 0)
        self.hitl_request_events += run_data.get("hitl_request_events", 0)
        self.hitl_response_events += run_data.get("hitl_response_events", 0)
        self.bitl_request_events += run_data.get("bitl_request_events", 0)
        self.bitl_response_events += run_data.get("bitl_response_events", 0)
        self.aitl_request_events += run_data.get("aitl_request_events", 0)
        self.aitl_response_events += run_data.get("aitl_response_events", 0)
        self.llm_cost += run_data.get("llm_cost", 0.0)

        run_started_at = run_data.get("started_at")
        run_ended_at = run_data.get("ended_at")

        if run_started_at:
            if self.first_event_time is None or run_started_at < self.first_event_time:
                self.first_event_time = run_started_at
        if run_ended_at:
            if self.latest_event_time is None or run_ended_at > self.latest_event_time:
                self.latest_event_time = run_ended_at

    def add_run_dto(self, run_dto: "RunStatistics"):
        """Adds a constructed RunStatistics DTO to the list."""
        self.runs.append(run_dto)
