from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.common.AddMemoryToChatHistoryEvent import AddMemoryToChatHistoryEvent


class AddUserMemoryToChatHistoryEvent(AddMemoryToChatHistoryEvent):
    """
    Specialized AddMemoryToChatHistoryEvent for user-specific memories.

    Emitted when an agent extends chat history with private user memories.
    The extended context contains personalized information specific to this user.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.add_user_memory_to_chat_history_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.add_user_memory_to_chat_history_event.description"
    )
