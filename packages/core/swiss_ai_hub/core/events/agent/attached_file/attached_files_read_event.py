from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class AttachedFilesReadEvent(ControlAndDisplayEvent):
    """The answer to `ReadAttachedFilesEvent`: one context block with every attached file, empty when there are none."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.attached_files_read_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.attached_files_read_event.description"
    )

    block: Annotated[
        list[ChatMessage], Field(description="System messages carrying the attached files' text, or none.")
    ] = []
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose it in a tool loop; none otherwise."),
    ] = None
