from typing import Annotated

from pydantic import BaseModel, Field


class GuardResult(BaseModel):
    """
    Base result model for all guard operations.

    This provides a consistent interface for guard decisions across the system,
    with reasoning for transparency and success status for control flow.
    """

    reasoning: Annotated[str, Field(description="Reasoning for the guard decision.")]
    success: Annotated[bool, Field(description="True if the guard allows the operation, false if it blocks it.")]
