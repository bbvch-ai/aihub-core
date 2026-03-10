from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class LimitChatHistoryEvent(ControlAndDisplayEvent):
    """
    Limits the chat messages based on number of input tokens.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.limit_chat_history_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.limit_chat_history_event.description"
    )

    limited_history: Annotated[
        list[ChatMessage], Field(description="Limited chat history based on number of input tokens.")
    ]
