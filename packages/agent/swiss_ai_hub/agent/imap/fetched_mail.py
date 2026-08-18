from pydantic import BaseModel
from swiss_ai_hub.core.events.agent import MailAttachmentRef, MailMessageRef

from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage


class FetchedMail(BaseModel):
    """A fetched message paired with the S3 references produced while archiving it.

    Keeps the parse result and its stored-object references together so a caller fetching a batch does not have to
    re-associate them afterwards. ``parsed`` still carries the untrusted ``body_html`` and the raw bytes, so this
    object never goes on an event — the references are what events carry.
    """

    parsed: ParsedMessage
    attachments: list[MailAttachmentRef] = []
    original_message: MailMessageRef | None = None
