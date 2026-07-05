from typing import Annotated

from pydantic import BaseModel, Field


class MailAttachmentRef(BaseModel):
    """Reference to a fetched mail attachment whose bytes are stored in S3, not carried in the event.

    Mirrors ``UserUploadedFile``: attachments are referenced by ``file_id`` (the S3 object key within the
    agent's dedicated bucket) so large binaries never bloat the persisted/streamed event.
    """

    filename: Annotated[str, Field(description="Original attachment filename, including extension.")]
    content_type: Annotated[str, Field(description="MIME type of the attachment.", examples=["application/pdf"])]
    file_id: Annotated[
        str,
        Field(description="UUID file identifier; the S3 object key is derived from the agent identity at runtime."),
    ]
    size_bytes: Annotated[int, Field(description="Size of the stored attachment in bytes.")]
