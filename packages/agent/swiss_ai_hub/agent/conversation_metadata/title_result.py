from typing import Annotated

from pydantic import BaseModel, Field


class TitleResult(BaseModel):
    """Structured LLM output for conversation title generation."""

    title: Annotated[
        str | None,
        Field(
            description=(
                "A concise title (3-6 words) capturing the topic of the conversation, in the language of the "
                "conversation. Null when the conversation has no identifiable topic yet (e.g. only greetings or "
                "small talk)."
            )
        ),
    ] = None
