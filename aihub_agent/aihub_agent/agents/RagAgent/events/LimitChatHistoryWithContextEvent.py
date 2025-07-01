from typing import Annotated, List

from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field


class LimitChatHistoryWithContextEvent(ControlEvent):
    """
    Limits the chat messages and the context information retrieved based on number of input tokens defined,
    """

    limited_history_with_context: Annotated[
        List[ChatMessage], Field(description="The limited chat history including the context information.")
    ]
