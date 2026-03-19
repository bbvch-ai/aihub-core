from typing import ClassVar

from swiss_ai_hub.core.i18n.locale_string import LocaleString

from .add_memory_to_chat_history_event import AddMemoryToChatHistoryEvent


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
