from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.auth.usage.models.limit_detail import LimitDetail
from swiss_ai_hub.core.auth.usage.usage_limit_models import UsageLimitPeriod


class ExceededDetail(BaseModel):
    """Structured 429 response body for usage limit exceeded errors."""

    error: Annotated[str, Field(description="Machine-readable error code")] = "usage_limit_exceeded"
    message: Annotated[str, Field(description="Pre-formatted, locale-aware display message")]
    current_count: Annotated[int | None, Field(description="Current call count of the most restrictive exceeded limit")]
    limit: Annotated[int | None, Field(description="Maximum allowed calls of the most restrictive exceeded limit")]
    period: Annotated[UsageLimitPeriod | None, Field(description="Time window of the most restrictive exceeded limit")]
    reset_at: Annotated[str | None, Field(description="ISO 8601 UTC reset timestamp")]
    reset_at_local: Annotated[str | None, Field(description="Local time (HH:MM) of reset")]
    reset_in_seconds: Annotated[int | None, Field(description="Seconds until counter resets")]
    limits: Annotated[list[LimitDetail], Field(description="All evaluated limits with their current status")]
