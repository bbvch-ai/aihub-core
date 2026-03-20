from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.events.agent import RetrieverEvent, StopEvent


class RetrievalResponseEvent(StopEvent, RetrieverEvent):
    """
    Event for returning a response from the retrieval agent containing the context message.
    """

    context_message: Annotated[ChatMessage, Field(description="The ordered modes as a context message.")]
