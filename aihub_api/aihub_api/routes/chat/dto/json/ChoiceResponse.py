from typing import Optional

from pydantic import BaseModel, Field

from aihub_api.routes.chat.dto.json.MessageResponse import MessageResponse


class ChoiceResponse(BaseModel):
    """
    Represents a single choice in a chat completion response, following OpenAI's API structure.
    """

    index: int = Field(
        ...,
        description="The index of this choice among all choices for this completion",
        example=0,
    )
    message: MessageResponse = Field(..., description="The message content of this choice")
    finish_reason: Optional[str] = Field(
        None,
        description="The reason why the model stopped generating, such as 'stop', 'length', or 'content_filter'",
        example="stop",
    )
