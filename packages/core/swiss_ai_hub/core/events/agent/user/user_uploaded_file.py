from typing import Annotated, ClassVar

from pydantic import BaseModel, Field


class UserUploadedFile(BaseModel):
    """Represents a file uploaded by a user for agent consumption.

    Security: Files are referenced by file_id only. The actual S3 location
    is derived at runtime from the agent's dedicated bucket, preventing IDOR.
    """

    filename: Annotated[
        str,
        Field(
            pattern=r"^[^/\\]+$",
            description="The name of the uploaded file, including the extension. Must not contain path separators.",
        ),
    ]
    file_type: Annotated[
        str, Field(description="The MIME type of the uploaded file.", examples=["image/png", "application/pdf"])
    ]
    file_id: Annotated[
        str,
        Field(
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            description="UUID4 file identifier, used as the S3 object key within the agent's dedicated bucket.",
        ),
    ]

    AGENT_FILES_BUCKET: ClassVar[str] = "agent-files"

    @staticmethod
    def _sanitize_path_segment(value: str) -> str:
        return value.replace("/", "_").replace("\\", "_").replace("..", "_")

    def resolve_s3_location(self, agent_class: str, agent_id: str) -> tuple[str, str]:
        """Derive the S3 bucket and key from the agent identity."""
        safe_class = self._sanitize_path_segment(agent_class)
        safe_id = self._sanitize_path_segment(agent_id)
        safe_file_id = self._sanitize_path_segment(self.file_id)
        safe_name = self._sanitize_path_segment(self.filename)
        key = f"{safe_class}/{safe_id}/{safe_file_id}/{safe_name}"
        return self.AGENT_FILES_BUCKET, key
