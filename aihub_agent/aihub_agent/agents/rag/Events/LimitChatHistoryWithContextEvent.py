from typing import List

from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryWithContextEvent(ControlEvent):
    """
    Event to limit the chat history with context.
    """
    limited_history_with_context: List[ChatMessage] = Field(..., description="The limited chat history with context.")
