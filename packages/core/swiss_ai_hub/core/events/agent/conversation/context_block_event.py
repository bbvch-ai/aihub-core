from typing import Annotated, Self

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class ContextBlockEvent(ControlEvent):
    """
    One enricher's contribution to the answer context: system-role messages the join step adds to the
    limited chat history ahead of the conversation.

    Every enricher a blueprint installs emits exactly one of these per turn, empty when it has nothing to
    add. That is what lets the join count blocks instead of knowing which enrichers exist or which are
    switched on — memory, fetched pages, attached files and search results all arrive through this one
    shape.
    """

    source: Annotated[str, Field(description="The enricher that produced the block, e.g. `user_memory`.")]
    messages: Annotated[
        list[ChatMessage],
        Field(description="System-role messages to add to the chat history. Empty when there was nothing to add."),
    ] = []

    @classmethod
    def empty(cls, source: str) -> Self:
        return cls(source=source, messages=[])

    @property
    def is_empty(self) -> bool:
        return not self.messages
