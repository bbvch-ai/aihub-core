from typing import Annotated, ClassVar, List

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class LimitChatHistoryEvent(ControlAndDisplayEvent):
    """
    Limits the chat messages based on number of input tokens.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.limit_chat_history_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.limit_chat_history_event.description"
    )

    limited_history: Annotated[
        List[ChatMessage], Field(description="Limited chat history based on number of input tokens.")
    ]
