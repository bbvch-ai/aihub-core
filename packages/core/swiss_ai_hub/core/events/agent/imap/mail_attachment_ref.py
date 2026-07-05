from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile


class MailAttachmentRef(BaseModel):
    """Reference to a fetched mail attachment whose bytes are stored in S3, not carried in the event.

    Mirrors ``UserUploadedFile``: attachments are referenced by ``file_id`` (the S3 object key within the
    agent's dedicated bucket) so large binaries never bloat the persisted/streamed event.
    """

    filename: Annotated[
        str,
        Field(
            pattern=r"^[^/\\]+$",
            description="Original attachment filename, including extension. Must not contain path separators.",
        ),
    ]
    content_type: Annotated[str, Field(description="MIME type of the attachment.", examples=["application/pdf"])]
    file_id: Annotated[
        str,
        Field(
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            description="UUID4 file identifier; the S3 object key is derived from the agent identity at runtime.",
        ),
    ]
    size_bytes: Annotated[int, Field(ge=0, description="Size of the stored attachment in bytes.")]

    def resolve_s3_location(self, agent_class: str, agent_id: str) -> tuple[str, str]:
        """Derive the S3 bucket and key through UserUploadedFile so both file contracts share one layout."""
        return UserUploadedFile(
            filename=self.filename,
            file_type=self.content_type,
            file_id=self.file_id,
        ).resolve_s3_location(agent_class, agent_id)
