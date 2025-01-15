from typing import List

from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryWithContextEvent(ControlEvent):
    """
    Limits the chat messages based on number of input tokens with context information.
    """
    limited_history_with_context: List[ChatMessage] = Field(..., description="The limited chat history with context.")
