from typing import List

from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class DecomposeQueryEvent(ControlEvent):
    """
    Event to decompose chat messages into a multiple questions.
    """

    decomposed_chat_history: ChatMessage = Field(
        ..., description="Decomposed chat history based on number of input tokens."
    )
