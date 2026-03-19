from typing import ClassVar

from swiss_ai_hub.core.i18n.locale_string import LocaleString

from .base_retrieve_memory_event import BaseRetrieveMemoryEvent


class RetrieveUserMemoryEvent(BaseRetrieveMemoryEvent):
    """
    Specialized BaseRetrieveMemoryEvent for user-specific memories.

    Emitted when an agent retrieves private user memories from long-term storage.
    These memories are scoped to individual users and never shared across users.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.retrieve_user_memory_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.retrieve_user_memory_event.description"
    )
