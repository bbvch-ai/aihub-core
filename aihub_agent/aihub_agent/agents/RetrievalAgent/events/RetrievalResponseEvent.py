from aihub_lib.nats.events import StopEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class RetrievalResponseEvent(StopEvent):
    context_message: ChatMessage = Field(..., description="The context message retrieved from the vector store.")
