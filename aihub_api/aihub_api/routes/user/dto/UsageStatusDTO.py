from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.auth.usage import UsageStatus


class LimitStatusDTO(BaseModel):
    """Response model for a single effective limit's status."""

    pattern: Annotated[str, Field(description="The matched pattern for this limit.")]
    limit: Annotated[int, Field(description="Maximum agent calls allowed per period.")]
    period: Annotated[str, Field(description="The period for the limit: 1h, 1d, 7d, 1mo.")]
    current_count: Annotated[int, Field(description="Current number of agent calls in this period.")]
    reset_at: Annotated[datetime | None, Field(description="When the usage counter resets.")]
    is_exceeded: Annotated[bool, Field(description="Whether this specific limit has been exceeded.")]


class UsageStatusDTO(BaseModel):
    """Response model representing a user's current usage status across all matching limits."""

    limits: Annotated[list[LimitStatusDTO], Field(description="All matching limits with their current status.")]
    is_exceeded: Annotated[bool, Field(description="Whether any usage limit has been exceeded.")]
    agent_path: Annotated[str | None, Field(description="The agent path this status refers to, if any.")] = None

    @classmethod
    def from_usage_status(cls, status: UsageStatus, agent_path: str | None = None) -> "UsageStatusDTO":
        return cls(
            limits=[
                LimitStatusDTO(
                    pattern=ls.pattern,
                    limit=ls.limit,
                    period=ls.period,
                    current_count=ls.current_count,
                    reset_at=ls.reset_at,
                    is_exceeded=ls.is_exceeded,
                )
                for ls in status.limits
            ],
            is_exceeded=status.is_exceeded,
            agent_path=agent_path,
        )
