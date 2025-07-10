from typing import Annotated

from pydantic import BaseModel, Field


class DatasetItem(BaseModel):
    id: Annotated[str | None, Field(description="The unique identifier for the dataset item, managed by Phoenix.")] = (
        None
    )
    question: Annotated[str, Field(description="The input question for the agent evaluation.")]
    answer: Annotated[str, Field(description="The reference (expected) answer for the question.")]
