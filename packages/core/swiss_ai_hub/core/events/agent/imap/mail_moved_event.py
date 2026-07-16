from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class MailMovedEvent(ControlAndDisplayEvent):
    """Records that a message was moved from its source folder into a target folder on the IMAP server."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.mail_moved_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.mail_moved_event.description"
    )

    message_id: Annotated[str, Field(description="IMAP UID of the moved message within its source folder.")]
    source_folder: Annotated[str, Field(description="Folder the message was moved out of.")]
    target_folder: Annotated[str, Field(description="Folder the message was moved into.")]
