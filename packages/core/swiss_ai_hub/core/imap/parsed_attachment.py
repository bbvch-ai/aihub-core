from pydantic import BaseModel


class ParsedAttachment(BaseModel):
    """An attachment parsed out of a MIME message, carrying its raw bytes before they are stored in S3."""

    filename: str
    content_type: str
    content: bytes
