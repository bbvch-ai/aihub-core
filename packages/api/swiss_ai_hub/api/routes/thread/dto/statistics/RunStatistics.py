from datetime import UTC, datetime
from typing import Annotated, Any, Self

from pydantic import Field

from swiss_ai_hub.api.routes.agent.dto.MinimalAgentInstanceDTO import MinimalAgentInstanceDTO
from swiss_ai_hub.api.routes.thread.dto.statistics.BaseEventStatistics import BaseEventStatistics


class RunStatistics(BaseEventStatistics):
    """Statistics for a single run, intended for API response."""

    run_id: Annotated[str, Field(description="The run ID")]
    agent: Annotated[MinimalAgentInstanceDTO, Field(description="The agent that ran the run")]

    @classmethod
    def from_run_data(
        cls,
        run_data: Annotated[dict[str, Any], "Data dict from aggregation pipeline"],
        agent_dto: Annotated[MinimalAgentInstanceDTO, "Pre-fetched agent DTO"],
    ) -> Self:
        """Creates a RunStatistics DTO from aggregation data and agent DTO."""
        run_started_at_dt: datetime | None = run_data.get("started_at")
        run_ended_at_dt: datetime | None = run_data.get("ended_at")

        started_at = run_started_at_dt
        if run_started_at_dt and run_started_at_dt.tzinfo is None:
            started_at = run_started_at_dt.replace(tzinfo=UTC)

        ended_at = run_ended_at_dt
        if run_ended_at_dt and run_ended_at_dt.tzinfo is None:
            ended_at = run_ended_at_dt.replace(tzinfo=UTC)

        return cls(
            run_id=run_data["run_id"],
            agent=agent_dto,
            n_events=run_data.get("n_events", 0),
            has_errors=run_data.get("has_errors", False),
            has_pending=run_data.get("has_pending", False),
            is_hitl=run_data.get("is_hitl", False),
            open_hitl=run_data.get("open_hitl", False),
            is_bitl=run_data.get("is_bitl", False),
            open_bitl=run_data.get("open_bitl", False),
            is_aitl=run_data.get("is_aitl", False),
            open_aitl=run_data.get("open_aitl", False),
            started_at=started_at.isoformat().replace("+00:00", "Z") if started_at else None,
            ended_at=ended_at.isoformat().replace("+00:00", "Z") if ended_at else None,
            duration=run_data.get("duration"),
        )
