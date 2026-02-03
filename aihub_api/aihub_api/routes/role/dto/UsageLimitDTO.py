from typing import Annotated

from aihub_lib.auth.usage import UsageLimitPeriod
from pydantic import BaseModel, Field, field_validator


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

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, value: str) -> str:
        """Validate pattern syntax: no empty segments, '>' only as last segment."""
        segments = value.split(".")
        if not segments or any(s == "" for s in segments):
            raise ValueError("Pattern must not contain empty segments")
        for i, segment in enumerate(segments):
            if segment == ">" and i != len(segments) - 1:
                raise ValueError("'>' wildcard must be the last segment in the pattern")
        return value
