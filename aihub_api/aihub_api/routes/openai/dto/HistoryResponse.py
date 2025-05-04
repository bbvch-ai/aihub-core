from typing import Annotated, List

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field


class HistoryResponse(BaseModel):
    messages: Annotated[List[ChatCompletionMessageParam], Field(description="Messages exchanged in this chat so far.")]
