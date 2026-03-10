from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.nats.events import ControlEvent


class LimitChatHistoryWithContextEvent(ControlEvent):
    """
    Limits the chat messages and the context information retrieved based on number of input tokens defined,
    """

    limited_history_with_context: Annotated[
        list[ChatMessage], Field(description="The limited chat history including the context information.")
    ]
