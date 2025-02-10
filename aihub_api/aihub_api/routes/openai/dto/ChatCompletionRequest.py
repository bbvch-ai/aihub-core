from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: Annotated[str, Field(description="ID of the model to use for the chat completion.")]
    stream: Annotated[bool, Field(description="Enable streaming response.")] = False
