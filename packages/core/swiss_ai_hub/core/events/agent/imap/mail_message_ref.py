from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile

RFC822_CONTENT_TYPE = "message/rfc822"


class MailMessageRef(BaseModel):
    """Reference to a fetched message's original RFC822 bytes, stored in S3 rather than carried in the event.

    Mirrors ``MailAttachmentRef``: the message is referenced by ``file_id`` so the raw mail — which may be
    orders of magnitude larger than the summary the event carries — never enters the audit trail or the
    WebSocket stream. The stored object is the message **verbatim**, so it also preserves what the event
    deliberately omits: the recipients and the untrusted HTML body.
    """

    filename: Annotated[
        str,
        Field(
            pattern=r"^[^/\\]+$",
            description="Filename the message is stored under, e.g. '1234.eml'. Must not contain path separators.",
        ),
    ]
    content_type: Annotated[str, Field(default=RFC822_CONTENT_TYPE, description="MIME type of the stored message.")]
    file_id: Annotated[
        str,
        Field(
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            description="UUID4 file identifier; the S3 object key is derived from the agent identity at runtime.",
        ),
    ]
    size_bytes: Annotated[int, Field(ge=0, description="Size of the stored message in bytes.")]

    @field_validator("filename")
    @classmethod
    def _reject_path_traversal(cls, value: str) -> str:
        """The pattern already blocks path separators; also reject ``..`` so the name can never walk
        directories when used in a download path or a ``Content-Disposition`` header."""
        if ".." in value:
            raise ValueError("filename must not contain '..'")
        return value

    def resolve_s3_location(self, agent_class: str, agent_id: str) -> tuple[str, str]:
        """Derive the S3 bucket and key through UserUploadedFile so every file contract shares one layout."""
        return UserUploadedFile(
            filename=self.filename,
            file_type=self.content_type,
            file_id=self.file_id,
        ).resolve_s3_location(agent_class, agent_id)
