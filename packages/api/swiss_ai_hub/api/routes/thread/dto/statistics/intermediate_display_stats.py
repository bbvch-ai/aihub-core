from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.thread.dto.statistics.run_statistics import RunStatistics


class IntermediateDisplayStats(BaseModel):
    """
    Internal model to accumulate stats for a display during processing.
    Uses datetime objects internally. Not intended for direct API response.
    """

    display_id: Annotated[str, Field(..., description="Unique identifier for the display")]
    runs: Annotated[list[RunStatistics], Field(description="List of run statistics for this display")] = []

    # Raw counts
    n_events: Annotated[int, Field(..., description="Total number of events in this display")] = 0
    start_events: Annotated[int, Field(..., description="Number of start events in this display")] = 0
    stop_events: Annotated[int, Field(..., description="Number of stop events in this display")] = 0
    exception_events: Annotated[int, Field(..., description="Number of exception events in this display")] = 0
    hitl_request_events: Annotated[int, Field(..., description="Number of Human-In-The-Loop request events")] = 0
    hitl_response_events: Annotated[int, Field(..., description="Number of Human-In-The-Loop response events")] = 0
    bitl_request_events: Annotated[int, Field(..., description="Number of Bot-In-The-Loop request events")] = 0
    bitl_response_events: Annotated[int, Field(..., description="Number of Bot-In-The-Loop response events")] = 0
    aitl_request_events: Annotated[int, Field(..., description="Number of AI-In-The-Loop request events")] = 0
    aitl_response_events: Annotated[int, Field(..., description="Number of AI-In-The-Loop response events")] = 0
    llm_cost: Annotated[float, Field(..., description="Total cost incurred by LLM operations")] = 0.0

    first_event_time: Annotated[
        datetime | None, Field(None, description="Timestamp of the first event in this display")
    ] = None
    latest_event_time: Annotated[
        datetime | None, Field(None, description="Timestamp of the most recent event in this display")
    ] = None

    def update_from_run_data(self, run_data: dict[str, Any]):
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
