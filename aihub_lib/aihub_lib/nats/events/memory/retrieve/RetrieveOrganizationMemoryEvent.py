from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString

from .BaseRetrieveMemoryEvent import BaseRetrieveMemoryEvent


class RetrieveOrganizationMemoryEvent(BaseRetrieveMemoryEvent):
    """
    Specialized BaseRetrieveMemoryEvent for organization-wide memories.

    Emitted when an agent retrieves shared organizational memories from long-term storage.
    These memories are accessible to all users within the organization namespace.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.retrieve_organization_memory_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.retrieve_organization_memory_event.description"
    )
