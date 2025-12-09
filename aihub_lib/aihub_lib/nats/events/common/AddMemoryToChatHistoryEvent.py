from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class AddMemoryToChatHistoryEvent(ControlAndDisplayEvent):
    extended_history: Annotated[list[ChatMessage], Field(description="Chat history extended with user memories.")]
