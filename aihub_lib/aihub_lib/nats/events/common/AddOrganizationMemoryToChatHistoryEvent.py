from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.common.AddMemoryToChatHistoryEvent import AddMemoryToChatHistoryEvent


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
