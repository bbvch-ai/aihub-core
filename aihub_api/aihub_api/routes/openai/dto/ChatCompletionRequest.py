from pydantic import BaseModel, ConfigDict, Field


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str = Field(..., description="ID of the model to use for the chat completion.")
    stream: bool = Field(False, description="Enable streaming response.")
