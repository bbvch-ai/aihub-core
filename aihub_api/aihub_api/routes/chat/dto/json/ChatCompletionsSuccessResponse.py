import uuid
from datetime import datetime, timezone
from typing import List

from aihub_lib.generative_ai.resources.costs.LLMCosts import LLMCosts
from pydantic import BaseModel, Field

from aihub_api.routes.chat.dto.json.ChoiceResponse import ChoiceResponse
from aihub_api.routes.chat.dto.json.MessageResponse import MessageResponse
from aihub_api.routes.chat.dto.json.UsageResponse import UsageResponse


class ChatCompletionsSuccessResponse(BaseModel):
    """
    Represents a successful response for chat completions, closely following OpenAI's API structure.
    This includes usage information in addition to the completion details.
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
    usage: UsageResponse = Field(..., description="Usage statistics for the completion request")

    @staticmethod
    def from_string(content: str, costs: LLMCosts, model: str = "bbv-ai-hub") -> "ChatCompletionsSuccessResponse":
        return ChatCompletionsSuccessResponse(
            id=str(uuid.uuid4()),
            object="chat.completion",
            created=int(datetime.now(timezone.utc).timestamp()),
            model=model,
            choices=[
                ChoiceResponse(
                    index=0,
                    message=MessageResponse(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            usage=UsageResponse(
                prompt_tokens=costs.prompt_token_count,
                completion_tokens=costs.completion_token_count,
                total_tokens=(costs.prompt_token_count + costs.completion_token_count),
            ),
        )
