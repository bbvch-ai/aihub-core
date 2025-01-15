from typing import List

from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryEvent(ControlEvent):
    """
    Event to limit the chat history.
    """
    limited_history: List[ChatMessage] = Field(..., description="The limited chat history.")
