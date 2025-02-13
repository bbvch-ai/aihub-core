from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class DecomposeQueryEvent(ControlEvent):
    """
    Event of decomposed chat messages into multiple queries.
    """

    decomposed_query: ChatMessage = Field(..., description="Decomposed chat history into one of multiple queries.")
