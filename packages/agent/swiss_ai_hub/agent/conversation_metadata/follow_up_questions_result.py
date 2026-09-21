from typing import Annotated

from pydantic import BaseModel, Field


class FollowUpQuestionsResult(BaseModel):
    """Structured LLM output for suggested follow-up questions."""

    questions: Annotated[
        list[str],
        Field(
            description=(
                "Between one and three follow-up questions the user might want to ask next, phrased from the user's "
                "perspective and in the language of the conversation. Empty when no useful follow-up exists."
            )
        ),
    ] = []
