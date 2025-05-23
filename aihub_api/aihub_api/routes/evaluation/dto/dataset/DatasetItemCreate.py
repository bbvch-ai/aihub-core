from typing import Annotated

from pydantic import BaseModel, Field


class DatasetItemCreate(BaseModel):
    question: Annotated[str, Field(description="The input question for the agent evaluation.")]
    answer: Annotated[str, Field(description="The reference (expected) answer for the question.")]
