from typing import ClassVar, List

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent


class LimitChatHistoryEvent(ControlEvent, DisplayEvent):
    """
    Limits the chat messages based on number of input tokens.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.limit_chat_history_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.limit_chat_history_event.description"
    )

    limited_history: List[ChatMessage] = Field(..., description="Limited chat history based on number of input tokens.")
