from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field


class UsageLimitPeriod(StrEnum):
    """Supported usage limit periods."""

    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"
    ONE_MONTH = "1mo"

    @property
    def seconds(self) -> int:
        """Duration of this period in seconds."""
        match self:
            case UsageLimitPeriod.ONE_HOUR:
                return 3600
            case UsageLimitPeriod.ONE_DAY:
                return 86400
            case UsageLimitPeriod.SEVEN_DAYS:
                return 604800
            case UsageLimitPeriod.ONE_MONTH:
                return 2592000


class RoleUsageLimit(BaseModel):
    """Typed representation of a single usage limit rule from a role."""

    pattern: Annotated[str, Field(description="Full dotted resource pattern with optional wildcards")]
    limit: Annotated[int, Field(ge=0, description="Maximum number of allowed calls in the period")]
    period: Annotated[UsageLimitPeriod, Field(description="Time window for the limit (1h, 1d, 7d, 1mo)")]


class RoleUsageLimitStatus(RoleUsageLimit):
    """Runtime status for one effective limit."""

    current_count: Annotated[int, Field(ge=0, description="Number of calls made in the current period")]
    reset_at: Annotated[datetime | None, Field(description="UTC timestamp when the counter resets")]
    is_exceeded: Annotated[bool, Field(description="Whether the limit has been reached or exceeded")]


class UsageStatus(BaseModel):
    """Current usage status for a user across all matching limits."""

    limits: Annotated[list[RoleUsageLimitStatus], Field(description="Status of each applicable limit")]
    is_exceeded: Annotated[bool, Field(description="Whether any limit has been exceeded")]

    @property
    def limit(self) -> int | None:
        """Most restrictive limit value — the exceeded or closest-to-exceeded limit."""
        entry = self._most_restrictive
        return entry.limit if entry else None

    @property
    def period(self) -> UsageLimitPeriod | None:
        """Period of the most restrictive limit."""
        entry = self._most_restrictive
        return entry.period if entry else None

    @property
    def current_count(self) -> int:
        """Current count of the most restrictive limit."""
        entry = self._most_restrictive
        return entry.current_count if entry else 0

    @property
    def reset_at(self) -> datetime | None:
        """Reset timestamp of the most restrictive limit."""
        entry = self._most_restrictive
        return entry.reset_at if entry else None

    @property
    def _most_restrictive(self) -> RoleUsageLimitStatus | None:
        """The exceeded limit (first found) or the one closest to being exceeded."""
        if not self.limits:
            return None
        for entry in self.limits:
            if entry.is_exceeded:
                return entry
        return max(self.limits, key=lambda entry: entry.current_count / entry.limit if entry.limit > 0 else 0)


class ResourceType(StrEnum):
    """Known resource type prefixes for usage limits."""

    AGENT = "agent"
