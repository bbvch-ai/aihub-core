from typing import Optional

from pydantic import BaseModel, Field

from api_core.routes.chat.dto.stream.ChoiceDelta import ChoiceDelta


class ChoiceStreamResponse(BaseModel):
    """
    Represents a single choice in a streaming chat completion response, following OpenAI's API structure.
    """

    index: int = Field(
        ...,
        description="The index of this choice among all choices for this completion chunk",
        example=0,
    )
    finish_reason: Optional[str] = Field(
        None,
        description="The reason why the model stopped generating, if applicable. Can be 'stop', 'length', 'content_filter', or None if still generating",
        example="stop",
    )
    delta: ChoiceDelta = Field(
        ...,
        description="The content delta (change) for this chunk of the response",
    )
