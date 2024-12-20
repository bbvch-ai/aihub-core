from typing import List

from pydantic import BaseModel, Field

from aihub_api.routes.chat.dto.json.ChoiceResponse import ChoiceResponse


class ChatCompletionsResponse(BaseModel):
    """
    Represents the response format for chat completions, closely following OpenAI's API structure.
    """

    id: str = Field(
        ...,
        description="A unique identifier for the chat completion",
        example="chatcmpl-123abc",
    )
    object: str = Field(
        ...,
        description="The object type, which is always 'chat.completion'",
        example="chat.completion",
    )
    created: int = Field(
        ...,
        description="The Unix timestamp (in seconds) of when the chat completion was created",
        example=1677858242,
    )
    model: str = Field(
        ...,
        description="The model used for the chat completion",
        example="gpt-3.5-turbo-0613",
    )
    choices: List[ChoiceResponse] = Field(
        ...,
        description="A list of chat completion choices. Can be more than one if n is greater than 1",
    )
