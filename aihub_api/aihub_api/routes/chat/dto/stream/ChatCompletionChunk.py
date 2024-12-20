import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from aihub_api.routes.chat.dto.stream.ChoiceDelta import ChoiceDelta
from aihub_api.routes.chat.dto.stream.ChoiceStreamResponse import ChoiceStreamResponse


class ChatCompletionChunk(BaseModel):
    """
    Represents a chunk of a streaming chat completion response, similar to OpenAI's API but with custom extensions.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this completion",
        example="chatcmpl-123abc",
    )
    object: str = Field(
        ...,
        description="Object type, always 'chat.completion.chunk' for streaming",
        example="chat.completion.chunk",
    )
    created: int = Field(
        ...,
        description="Unix timestamp (in seconds) of when this chunk was created",
        example=1677858242,
    )
    model: str = Field(
        ...,
        description="The model used for generating this completion chunk",
        example="gpt-3.5-turbo-0613",
    )
    choices: List[ChoiceStreamResponse] = Field(
        ...,
        description="List of completion choices for this chunk, typically contains one item for streaming",
    )
    usage: Optional[Union[str, Dict]] = Field(
        None,
        description="Optional usage information, can be a string or a dictionary",
    )

    @classmethod
    def from_string(
        cls,
        content: str,
        model: str = "bbv-ai-hub",
        finish_reason: Optional[str] = None,
    ) -> "ChatCompletionChunk":
        return ChatCompletionChunk(
            id=str(uuid.uuid4()),
            object="chat.completion.chunk",
            created=int(datetime.now(timezone.utc).timestamp()),
            model=model,
            choices=[
                ChoiceStreamResponse(
                    index=0,
                    delta=ChoiceDelta(content=content, role="assistant"),
                    finish_reason=finish_reason,
                )
            ],
            usage=None,
        )
