from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.imap.mail_attachment_ref import MailAttachmentRef
from swiss_ai_hub.core.events.agent.imap.mail_message_ref import MailMessageRef


class MailClassificationRef(BaseModel):
    """One classified message and where it was filed — the per-message detail behind a run summary."""

    message_id: Annotated[str, Field(description="IMAP UID of the message within the source folder.")]
    sender: Annotated[str, Field(description="Raw From header of the message.")]
    subject: Annotated[str, Field(description="Subject header of the message.")]
    category: Annotated[
        str | None,
        Field(
            default=None,
            description="Configured category the message was filed under, or null when it went to the fallback "
            "folder because no category clearly fitted.",
        ),
    ]
    target_folder: Annotated[str, Field(description="Folder the message was filed into.")]
    reason: Annotated[str, Field(description="Model's stated reason for the choice — the audit trail for a misfile.")]
    folder_created: Annotated[
        bool,
        Field(
            default=False,
            description="Whether this message's target folder was created during the run. Folders are created once "
            "up front for the whole batch, so every message routed to a newly created folder carries this, not only "
            "the first one.",
        ),
    ]
    attachments: Annotated[
        list[MailAttachmentRef],
        Field(default_factory=list, description="References to the message's attachments stored in S3."),
    ]
    original_message: Annotated[
        MailMessageRef | None,
        Field(default=None, description="Reference to the original RFC822 message stored in S3."),
    ]
