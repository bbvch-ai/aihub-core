import re
from typing import Annotated

from aihub_lib.generative_ai.document.types.FileTypeConfig import FileTypeConfig
from pydantic import BaseModel, Field, field_validator, model_validator


class DocumentUploadRequest(BaseModel):
    """
    Request payload for initiating file upload to knowledge base.

    This request is used to get presigned URLs for direct S3/MinIO upload
    of files that will be processed and indexed in the knowledge base.
    """

    filename: Annotated[str, Field(description="Original filename of the file", min_length=1, max_length=255)]
    content_type: Annotated[str, Field(description="MIME type of the file")]
    content_length: Annotated[int, Field(description="Size of the file in bytes", gt=0)]

    @classmethod
    @field_validator("filename")
    def validate_filename_format(cls, v: str) -> str:
        v = v.strip()
        # Regex enforces: Starts with safe char, no path chars, must end in .extension
        filename_pattern = r"^[^\x00-\x1f/\\][^\x00-\x1f/\\]*\.[a-zA-Z0-9]+$"
        if not re.match(filename_pattern, v):
            raise ValueError("Invalid filename format.")
        extension = v.rsplit(".", 1)[-1]
        if len(extension) > 10:
            raise ValueError("File extension is too long.")
        return v

    @model_validator(mode="after")
    def validate_file_type_and_consistency(self) -> "DocumentUploadRequest":
        """
        Performs file type validation using our extension-based allowlist and mimetypes.
        """
        try:
            mime_type = self.content_type.lower().split(";")[0].strip()
            file_ext = "." + self.filename.rsplit(".", 1)[-1].lower()
        except (AttributeError, IndexError):
            raise ValueError("Invalid filename or content_type format.")
        file_type = FileTypeConfig()
        # First check: Is the extension allowed?
        if not file_type.is_extension_supported(file_ext):
            supported_extensions = file_type.get_unique_extensions()
            raise ValueError(
                f"File extension '{file_ext}' is not supported. "
                f"Supported extensions: {', '.join(supported_extensions)}"
            )

        # Second check: Does the MIME type match what we expect for this extension?
        expected_mime_type = file_type.get_mime_type_for_extension(file_ext)
        if expected_mime_type and mime_type != expected_mime_type:
            raise ValueError(
                f"File extension '{file_ext}' does not match content type '{mime_type}'. "
                f"Expected MIME type: {expected_mime_type}"
            )

        self.content_type = mime_type
        return self
