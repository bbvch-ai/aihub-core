from typing import List

from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class DecomposeQueryEvent(ControlEvent):
    """
    Event of decomposed chat messages into multiple queries.
    """

    decomposed_query: ChatMessage = Field(..., description="Decomposed chat history into one of multiple queries.")
