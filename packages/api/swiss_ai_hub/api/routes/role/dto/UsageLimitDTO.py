from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.auth.access.AccessChecker import AccessChecker
from swiss_ai_hub.core.auth.usage import UsageLimitPeriod


class UsageLimitDTO(BaseModel):
    """Pattern-based usage limit rule."""

    pattern: Annotated[
        str,
        Field(
            description="Full dotted resource pattern with wildcards "
            "(e.g. 'aihub.user.agent.>', 'aihub.user.process.MyProcess.*'). "
        ),
    ]
    limit: Annotated[int, Field(ge=1, description="Max calls per period for this pattern.")]
    period: Annotated[UsageLimitPeriod, Field(description="Period for limit: 1h, 1d, 7d, 1mo.")]
    description: Annotated[str | None, Field(description="Human-readable description of the pattern.")] = None

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value: str) -> str:
        """Validate pattern using AccessChecker's canonical validation."""
        if not AccessChecker.validate_user_access_rule(value):
            raise ValueError(f"Invalid usage limit pattern: {value!r}")
        return value
