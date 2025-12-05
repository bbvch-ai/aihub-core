from typing import Annotated

from pydantic import BaseModel, Field


class SubmitAnswerRequest(BaseModel):
    """Request body for submitting an answer to an expert question."""

    response: Annotated[str, Field(description="The expert's answer to the question.", min_length=1)]
