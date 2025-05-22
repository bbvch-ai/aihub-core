from typing import Optional, Annotated
from pydantic import BaseModel, Field

class DatasetItem(BaseModel):
    id: Annotated[Optional[str], Field(description="The unique identifier for the dataset item, managed by Phoenix.")] = None
    question: Annotated[str, Field(description="The input question for the agent evaluation.")]
    answer: Annotated[str, Field(description="The reference (expected) answer for the question.")]