from __future__ import annotations

from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.auth.usage.usage_limit_models import RoleUsageLimit


class LimitDetail(RoleUsageLimit):
    """One limit entry in the exceeded-detail response, extending the base limit with presentation fields."""

    scope: Annotated[dict[str, str], Field(description="Localized scope labels keyed by locale")]
    period_label: Annotated[dict[str, str], Field(description="Localized period labels keyed by locale")]
    current_count: Annotated[int, Field(ge=0, description="Number of calls made in the current period")]
    is_exceeded: Annotated[bool, Field(description="Whether the current count has reached or exceeded the limit")]
