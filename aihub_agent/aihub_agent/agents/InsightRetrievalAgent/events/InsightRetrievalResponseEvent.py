from typing import Annotated

from aihub_lib.nats.events import RetrieverEvent, StopEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class InsightRetrievalResponseEvent(StopEvent, RetrieverEvent):
    """
    Response event from the InsightRetrievalAgent containing the context message and retrieved nodes.
    """

    context_message: Annotated[ChatMessage, Field(description="The ordered nodes as a context message.")]
