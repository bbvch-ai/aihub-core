from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class MemoryRecalledEvent(ControlEvent):
    """The answer to `RecallMemoryEvent`: one context block per memory scope, each empty when nothing applies."""

    user_block: Annotated[
        list[ChatMessage], Field(description="System messages carrying the user's memories, or none.")
    ] = []
    organization_block: Annotated[
        list[ChatMessage], Field(description="System messages carrying the organization's memories, or none.")
    ] = []
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose it in a tool loop; none otherwise."),
    ] = None

    @property
    def blocks(self) -> list[list[ChatMessage]]:
        """User memory first: the more personal context leads."""
        return [self.user_block, self.organization_block]
