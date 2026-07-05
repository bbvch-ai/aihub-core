from datetime import datetime

from pydantic import BaseModel


class ParsedAttachment(BaseModel):
    """An attachment parsed out of a MIME message, carrying its raw bytes before they are stored in S3."""

    filename: str
    content_type: str
    content: bytes


class ParsedMessage(BaseModel):
    """A fully parsed MIME message — headers, decoded bodies, and attachments with their raw bytes."""

    message_id: str
    sender: str
    subject: str
    date: datetime | None = None
    body_text: str | None = None
    body_html: str | None = None
    attachments: list[ParsedAttachment] = []
