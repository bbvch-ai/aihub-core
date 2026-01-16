from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class UserUsageDTO(BaseModel):
    """User usage and budget information from LiteLLM."""

    user_id: Annotated[str, Field(description="The user's unique identifier")]
    spend: Annotated[float, Field(description="Total spend in USD for current period", ge=0)]
    max_budget: Annotated[float | None, Field(description="Maximum budget limit in USD (None if unlimited)")]
    soft_budget: Annotated[float | None, Field(description="Soft budget threshold for alerts in USD")]
    budget_duration: Annotated[str | None, Field(description="Budget reset period (e.g., '1mo', '30d')")]
    budget_reset_at: Annotated[datetime | None, Field(description="When the budget will reset")]
    tpm_limit: Annotated[int | None, Field(description="Tokens per minute limit")]
    rpm_limit: Annotated[int | None, Field(description="Requests per minute limit")]
    usage_percent: Annotated[float | None, Field(description="Percentage of budget used (0-100)", ge=0, le=100)]
    is_approaching_limit: Annotated[bool, Field(description="True if usage is >= 80% of max_budget")]
    is_over_limit: Annotated[bool, Field(description="True if usage exceeds max_budget")]
