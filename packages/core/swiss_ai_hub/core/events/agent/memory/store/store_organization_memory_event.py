from typing import ClassVar

from swiss_ai_hub.core.i18n.locale_string import LocaleString

from .base_store_memory_event import BaseStoreMemoryEvent


class StoreOrganizationMemoryEvent(BaseStoreMemoryEvent):
    """
    Specialized BaseStoreMemoryEvent for organization-wide memories.

    Emitted when an agent stores shared organizational memories to long-term storage.
    These memories are accessible to all users within the organization namespace.
    Unlike user memories (inferred from chat), organization memories are explicit facts provided by users.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.store_organization_memory_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.store_organization_memory_event.description"
    )
