from typing import ClassVar

from swiss_ai_hub.core.i18n.locale_string import LocaleString

from .base_store_memory_event import BaseStoreMemoryEvent


class StoreUserMemoryEvent(BaseStoreMemoryEvent):
    """
    Specialized BaseStoreMemoryEvent for user-specific memories.

    Emitted when an agent stores private user memories to long-term storage.
    These memories are scoped to individual users and never shared across users.
    User memories are typically inferred from conversation context.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.new_memory_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.new_memory_event.description"
    )
