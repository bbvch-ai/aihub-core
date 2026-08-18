from datetime import datetime

from pydantic import BaseModel


class ParsedAttachment(BaseModel):
    """An attachment parsed out of a MIME message, carrying its raw bytes before they are stored in S3."""

    filename: str
    content_type: str
    content: bytes


class ParsedMessage(BaseModel):
    """A fully parsed MIME message — headers, decoded bodies, and attachments with their raw bytes.

    ``body_html`` is untrusted, sender-controlled markup. It is intentionally NOT surfaced on
    ``MailFetchedEvent`` (which is persisted and streamed to the frontend) — a consumer that needs it
    must sanitize it server-side first. It is kept here only as the in-process parse result.

    ``raw`` is the message exactly as the server sent it, kept so the original can be archived verbatim.
    Like ``body_html`` it never enters an event; it is written to S3 and referenced by ``MailMessageRef``.
    """

    message_id: str
    sender: str
    subject: str
    date: datetime | None = None
    rfc_message_id: str | None = None
    references: str | None = None
    reply_to: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    attachments: list[ParsedAttachment] = []
    raw: bytes = b""
