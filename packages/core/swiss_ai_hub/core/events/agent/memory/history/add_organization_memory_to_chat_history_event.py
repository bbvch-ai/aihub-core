from typing import ClassVar

from swiss_ai_hub.core.i18n.locale_string import LocaleString

from .add_memory_to_chat_history_event import AddMemoryToChatHistoryEvent


class AddOrganizationMemoryToChatHistoryEvent(AddMemoryToChatHistoryEvent):
    """
    Specialized AddMemoryToChatHistoryEvent for organization-wide memories.

    Emitted when an agent extends chat history with shared organizational memories.
    The extended context contains organizational knowledge accessible to all users.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.add_organization_memory_to_chat_history_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.add_organization_memory_to_chat_history_event.description"
    )
