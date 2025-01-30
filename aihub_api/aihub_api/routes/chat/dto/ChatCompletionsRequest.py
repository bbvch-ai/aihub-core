from typing import List, Optional

from llama_index.core.base.llms.types import ChatMessage
from pydantic import BaseModel, Field


class ChatCompletionsRequest(BaseModel):
    """
    Represents a request for chat completions, following OpenAI's API structure with custom extensions.
    """

    messages: List[ChatMessage] = Field(..., description="A list of messages comprising the conversation so far")
