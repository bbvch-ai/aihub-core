from typing import Annotated

from pydantic import BaseModel, Field


class JudgeOutput(BaseModel):
    """
    Defines the structured output expected from the LLM Judge for each evaluation.
    This ensures consistent, parseable results from the LLM calls.
    """

    score: Annotated[float, Field(description="The evaluation score, typically between 0.0 and 1.0.")]
    reasoning: Annotated[str, Field(description="A brief explanation for the assigned score.")]
    error: Annotated[
        bool | None,
        Field(description="Flag indicating if the judge encountered an issue evaluating."),
    ] = False
