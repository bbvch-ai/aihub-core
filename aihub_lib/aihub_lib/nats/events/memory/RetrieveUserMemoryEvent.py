from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.memory.RetrieveMemoryEvent import RetrieveMemoryEvent


class RetrieveUserMemoryEvent(RetrieveMemoryEvent):
    """
    Specialized RetrieveMemoryEvent for user-specific memories.

    Emitted when an agent retrieves private user memories from long-term storage.
    These memories are scoped to individual users and never shared across users.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.retrieve_user_memory_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.retrieve_user_memory_event.description"
    )
