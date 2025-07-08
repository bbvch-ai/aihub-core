from typing import Annotated

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field


class HistoryResponse(BaseModel):
    messages: Annotated[list[ChatCompletionMessageParam], Field(description="Messages exchanged in this chat so far.")]
