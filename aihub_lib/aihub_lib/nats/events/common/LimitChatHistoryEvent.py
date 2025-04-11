from typing import List

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent


class LimitChatHistoryEvent(ControlEvent, DisplayEvent):
    """
    Limits the chat messages based on number of input tokens.
    """

    limited_history: List[ChatMessage] = Field(..., description="Limited chat history based on number of input tokens.")
