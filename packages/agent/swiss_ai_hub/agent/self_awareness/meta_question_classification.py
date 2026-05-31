from typing import Annotated, Literal

from pydantic import BaseModel, Field

type MetaQuestionCategory = Literal["identity", "capabilities", "behavior"]


class MetaQuestionClassification(BaseModel):
    """Structured verdict of whether a user message is a meta question about the agent."""

    is_meta_question: Annotated[bool, Field(description="True if the message is about the assistant itself.")]
    category: Annotated[
        MetaQuestionCategory | None,
        Field(default=None, description="Which aspect the question is about; null if not a meta question."),
    ]
    reasoning: Annotated[str, Field(description="Brief justification for the classification.")]
