from typing import Annotated

from pydantic import BaseModel, Field


class TagsResult(BaseModel):
    """Structured LLM output for conversation tag generation."""

    tags: Annotated[
        list[str],
        Field(
            description=(
                "Between one and five short category tags describing the conversation, in the language of the "
                "conversation. Empty when the conversation has no identifiable topic yet."
            )
        ),
    ] = []
