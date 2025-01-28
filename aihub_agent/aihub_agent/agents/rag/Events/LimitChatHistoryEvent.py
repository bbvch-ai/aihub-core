from typing import List

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class LimitChatHistoryEvent(ControlEvent):
    """
    Limits the chat messages based on number of input tokens.
    """

    limited_history: List[ChatMessage] = Field(..., description="Limited chat history based on number of input tokens.")
