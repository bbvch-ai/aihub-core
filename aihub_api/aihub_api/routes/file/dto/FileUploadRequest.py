import re
from typing import Annotated

from aihub_lib.generative_ai.document.types.FileTypeConfig import SUPPORTED_FILE_TYPES_CONFIG
from pydantic import BaseModel, Field, field_validator, model_validator


class FileUploadRequest(BaseModel):
    """
    Request payload for initiating file upload to knowledge base.

    This request is used to get presigned URLs for direct S3/MinIO upload
    of files that will be processed and indexed in the knowledge base.
    """

    filename: Annotated[str, Field(description="Original filename of the file", min_length=1, max_length=255)]
    content_type: Annotated[str, Field(description="MIME type of the file")]
    content_length: Annotated[int, Field(description="Size of the file in bytes", gt=0)]
    namespace_name: Annotated[str, Field(description="Target namespace name")]
    database_name: Annotated[str, Field(description="Target database name")]

    @classmethod
    @field_validator("filename")
    def validate_filename_format(cls, v: str) -> str:
        v = v.strip()
        filename_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*(\.[a-zA-Z0-_ \-]+)*\.[a-zA-Z0-9]+$"
        if not re.match(filename_pattern, v):
            raise ValueError("Invalid filename format.")
        if any(pattern in v for pattern in ["..", "/", "\\", "\x00"]):
            raise ValueError("Filename contains forbidden characters or sequences.")
        parts = v.split(".")
        if len(parts) > 3:
            raise ValueError("Filename has too many extensions.")
        if len(parts[-1]) > 10:
            raise ValueError("File extension is too long.")
        return v

    @classmethod
    @field_validator("namespace_name", "database_name")
    def validate_names(cls, v: str) -> str:
        name_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$"
        if not re.match(name_pattern, v):
            raise ValueError("Invalid name format.")
        if any(pattern in v for pattern in ["..", "/", "\\", "\x00"]):
            raise ValueError("Name contains forbidden characters.")
        return v

    @model_validator(mode="after")
    def validate_file_type_and_consistency(self) -> "FileUploadRequest":
        """
        Performs file type validation by asking the central config service.
        """
        try:
            mime_type = self.content_type.lower().split(";")[0].strip()
            file_ext = "." + self.filename.split(".")[-1].lower()
        except (AttributeError, IndexError):
            raise ValueError("Invalid filename or content_type format.")

        if not SUPPORTED_FILE_TYPES_CONFIG.is_mime_type_supported(mime_type):
            raise ValueError(f"Content type '{mime_type}' is not supported.")

        if not SUPPORTED_FILE_TYPES_CONFIG.is_extension_supported(file_ext):
            raise ValueError(f"File extension '{file_ext}' is not supported.")

        if not SUPPORTED_FILE_TYPES_CONFIG.is_pair_consistent(file_ext, mime_type):
            allowed = SUPPORTED_FILE_TYPES_CONFIG.get_allowed_extensions_for_mime(mime_type)
            raise ValueError(
                f"File extension '{file_ext}' does not match content type '{mime_type}'. "
                f"Expected one of: {', '.join(allowed or [])}"
            )

        self.content_type = mime_type
        return self
