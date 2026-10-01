from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class AttachedFilesReadEvent(ControlEvent):
    """The answer to `ReadAttachedFilesEvent`: one context block with every attached file, empty when there are none."""

    block: Annotated[
        list[ChatMessage], Field(description="System messages carrying the attached files' text, or none.")
    ] = []
