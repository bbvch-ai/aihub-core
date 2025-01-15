from typing import List

from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryEvent(ControlEvent):
    """
    Limits the chat messages based on number of input tokens.
    """
    limited_history: List[ChatMessage] = Field(..., description="The limited chat history.")
