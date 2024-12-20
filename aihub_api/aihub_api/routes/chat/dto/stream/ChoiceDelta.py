from typing import Optional

from pydantic import BaseModel, Field


class ChoiceDelta(BaseModel):
    """
    Represents the delta (change) in a streaming chat completion response, following OpenAI's structure.
    """

    role: Optional[str] = Field(
        None,
        description="The role for this message chunk, if this is the first chunk of a new message",
    )
    content: Optional[str] = Field(None, description="The content chunk for this part of the message")
