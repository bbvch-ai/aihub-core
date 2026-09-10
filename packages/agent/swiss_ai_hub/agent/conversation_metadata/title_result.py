from typing import Annotated

from pydantic import BaseModel, Field


class TitleResult(BaseModel):
    """Structured LLM output for conversation title generation."""

    title: Annotated[
        str,
        Field(
            description=(
                "A concise title (3-6 words) capturing the topic of the conversation, in the language of the "
                "conversation. Even a greeting or small talk gets a plain, natural title (e.g. 'Greeting') — "
                "never empty."
            )
        ),
    ]
