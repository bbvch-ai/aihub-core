from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.imap.mail_attachment_ref import MailAttachmentRef
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class MailFetchedEvent(ControlAndDisplayEvent):
    """Carries a single fetched message — headers, body, and references to its stored attachments."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.mail_fetched_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.mail_fetched_event.description"
    )

    message_id: Annotated[str, Field(description="IMAP UID of the fetched message within the inbox folder.")]
    sender: Annotated[str, Field(description="Raw From header of the message.")]
    subject: Annotated[str, Field(description="Subject header of the message.")]
    date: Annotated[datetime | None, Field(default=None, description="Date header of the message, if parseable.")]
    body_text: Annotated[str | None, Field(default=None, description="Plain-text body of the message, if present.")]
    attachments: Annotated[
        list[MailAttachmentRef],
        Field(default_factory=list, description="References to the message's attachments stored in S3."),
    ]
