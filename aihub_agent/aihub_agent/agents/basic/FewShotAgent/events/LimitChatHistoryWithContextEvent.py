from typing import List

from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage


class LimitChatHistoryWithContextEvent(ControlEvent):
    """
    Limits the chat messages and the context information retrieved based on number of input tokens defined,
    """
    limited_history_with_context: List[ChatMessage] = Field(..., description="The limited chat history including the context information.")
