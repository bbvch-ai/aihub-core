import logging
from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.api.routes.thread.dto.statistics.base_event_statistics import BaseEventStatistics
from swiss_ai_hub.api.routes.thread.dto.statistics.intermediate_display_stats import IntermediateDisplayStats
from swiss_ai_hub.api.routes.thread.dto.statistics.run_statistics import RunStatistics

logger = logging.getLogger(__name__)

_UTC_OFFSET_SUFFIX = "+00:00"


class DisplayStatistics(BaseEventStatistics):
    """Statistics for a display, including its runs, intended for API response."""

    display_id: Annotated[str, Field(description="The display ID")]
    runs: Annotated[list[RunStatistics], Field(description="Runs in this display, sorted by start time")] = []

    @classmethod
    def from_intermediate(
        cls,
        intermediate: Annotated[IntermediateDisplayStats, "Input is the accumulated intermediate stats"],
    ) -> Self:
        """Creates a DisplayStatistics DTO from an IntermediateDisplayStats object."""

        # Calculate derived boolean flags for the display from intermediate counts
        has_pending = intermediate.start_events > (intermediate.stop_events + intermediate.exception_events)
        has_errors = intermediate.exception_events > 0
        is_hitl = intermediate.hitl_request_events > 0
        open_hitl = intermediate.hitl_request_events > intermediate.hitl_response_events
        is_bitl = intermediate.bitl_request_events > 0
        open_bitl = intermediate.bitl_request_events > intermediate.bitl_response_events
        is_aitl = intermediate.aitl_request_events > 0
        open_aitl = intermediate.aitl_request_events > intermediate.aitl_response_events

        # Calculate duration from intermediate datetime objects
        duration = None
        started_at_dt = intermediate.first_event_time
        ended_at_dt = intermediate.latest_event_time
        if started_at_dt and ended_at_dt:
            duration = (ended_at_dt - started_at_dt).total_seconds()

        def sort_key(run: RunStatistics):
            started_at_str = run.started_at
            if started_at_str:
                try:
                    return datetime.fromisoformat(started_at_str.replace("Z", _UTC_OFFSET_SUFFIX))
                except ValueError:
                    logger.exception(f"Could not parse run start time for sorting: {started_at_str}")
                    return datetime.min.replace(tzinfo=UTC)  # Fallback
            # Place runs with no start time at the beginning or end consistently
            return datetime.min.replace(tzinfo=UTC)

        sorted_runs = sorted(intermediate.runs, key=sort_key)

        started_at = started_at_dt
        if started_at_dt and started_at_dt.tzinfo is None:
            started_at = started_at_dt.replace(tzinfo=UTC)

        ended_at = ended_at_dt
        if ended_at_dt and ended_at_dt.tzinfo is None:
            ended_at = ended_at_dt.replace(tzinfo=UTC)

        return cls(
            display_id=intermediate.display_id,
            runs=sorted_runs,
            n_events=intermediate.n_events,
            has_errors=has_errors,
            has_pending=has_pending,
            is_hitl=is_hitl,
            open_hitl=open_hitl,
            is_bitl=is_bitl,
            open_bitl=open_bitl,
            is_aitl=is_aitl,
            open_aitl=open_aitl,
            started_at=started_at.isoformat().replace(_UTC_OFFSET_SUFFIX, "Z") if started_at else None,
            ended_at=ended_at.isoformat().replace(_UTC_OFFSET_SUFFIX, "Z") if ended_at else None,
            duration=duration,
        )
