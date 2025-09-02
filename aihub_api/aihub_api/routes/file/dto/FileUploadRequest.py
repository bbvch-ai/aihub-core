import re
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator


class FileUploadRequest(BaseModel):
    """
    Request payload for initiating file upload to knowledge base.

    This request is used to get presigned URLs for direct S3/MinIO upload
    of files that will be processed and indexed in the knowledge base.
    """

    ALLOWED_CONTENT_TYPES: ClassVar[dict[str, list[str]]] = {
        # Text documents
        "text/plain": [".txt", ".asc"],
        "text/markdown": [".md", ".markdown"],
        "text/x-markdown": [".md", ".markdown"],
        "text/csv": [".csv"],
        "text/html": [".html", ".htm", ".xhtml"],
        "application/xhtml+xml": [".xhtml"],
        "text/asciidoc": [".adoc", ".asciidoc", ".asc"],
        "text/x-asciidoc": [".adoc", ".asciidoc", ".asc"],
        # PDF
        "application/pdf": [".pdf"],
        # Microsoft Office documents (Word)
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.template": [".dotx"],
        "application/vnd.ms-word.document.macroenabled.12": [".docm"],
        "application/vnd.ms-word.template.macroenabled.12": [".dotm"],
        # Microsoft Office documents (PowerPoint)
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"],
        "application/vnd.openxmlformats-officedocument.presentationml.template": [".potx"],
        "application/vnd.openxmlformats-officedocument.presentationml.slideshow": [".ppsx"],
        "application/vnd.ms-powerpoint.presentation.macroenabled.12": [".pptm"],
        "application/vnd.ms-powerpoint.template.macroenabled.12": [".potm"],
        "application/vnd.ms-powerpoint.slideshow.macroenabled.12": [".ppsm"],
        # Microsoft Office documents (Excel)
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
        "application/vnd.ms-excel.sheet.macroenabled.12": [".xlsm"],
        # Data formats
        "application/json": [".json"],
        "application/xml": [".xml", ".nxml"],
        "text/xml": [".xml", ".nxml"],
        # Images
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"],
        "image/tiff": [".tif", ".tiff"],
        "image/bmp": [".bmp"],
        "image/webp": [".webp"],
        # Audio
        "audio/wav": [".wav"],
        "audio/wave": [".wav"],
        "audio/x-wav": [".wav"],
        "audio/mpeg": [".mp3"],
        "audio/mp3": [".mp3"],
    }

    filename: Annotated[str, Field(description="Original filename of the file", min_length=1, max_length=255)]
    content_type: Annotated[str, Field(description="MIME type of the file")]
    content_length: Annotated[
        int,
        Field(
            description="Size of the file in bytes",
            gt=0,
        ),
    ]
    namespace_name: Annotated[str, Field(description="Target namespace name")]
    database_name: Annotated[str, Field(description="Target database name")]

    @classmethod
    def get_extension_to_content_types(cls) -> dict[str, list[str]]:
        ext_to_types: dict[str, list[str]] = {}
        for content_type, extensions in cls.ALLOWED_CONTENT_TYPES.items():
            for ext in extensions:
                if ext not in ext_to_types:
                    ext_to_types[ext] = []
                ext_to_types[ext].append(content_type)
        return ext_to_types

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        v = v.strip()

        # Pattern: start with alphanumeric, then allow alphanumeric/space/dash/underscore, must end with extension
        filename_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*(\.[a-zA-Z0-9_\-]+)*\.[a-zA-Z0-9]+$"

        if not re.match(filename_pattern, v):
            raise ValueError(
                "Invalid filename format. Filenames must: "
                "1) Start with alphanumeric character, "
                "2) Contain only letters, numbers, spaces, dashes, underscores, and dots, "
                "3) Have a file extension, "
                "4) Not contain path separators or special characters"
            )

        if any(pattern in v for pattern in ["..", "/", "\\", "\x00", "\n", "\r", "\t"]):
            raise ValueError("Filename contains forbidden characters or sequences")

        parts = v.split(".")
        if len(parts) > 3:  # e.g., filename.tar.gz would be 3 parts max
            raise ValueError("Filename has too many extensions")

        if len(parts[-1]) > 10:
            raise ValueError("File extension is too long")

        file_ext = "." + parts[-1].lower()
        ext_to_types = cls.get_extension_to_content_types()

        if file_ext not in ext_to_types:
            allowed_extensions = sorted(ext_to_types.keys())
            raise ValueError(
                f"File type '{file_ext}' is not supported. " f"Allowed types: {', '.join(allowed_extensions)}"
            )

        return v

    @field_validator("namespace_name", "database_name")
    @classmethod
    def validate_names(cls, v: str) -> str:
        """
        Validate namespace and database names to prevent injection attacks.
        Allow spaces for user-friendly names.
        """
        # Must start with alphanumeric, then allow alphanumeric/space/dash/underscore
        name_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$"

        if not re.match(name_pattern, v):
            raise ValueError(
                "Invalid name. Names must start with alphanumeric character "
                "and contain only letters, numbers, spaces, dashes, and underscores"
            )

        if any(pattern in v for pattern in ["..", "/", "\\", "\x00", "\n", "\r", "\t"]):
            raise ValueError("Name contains forbidden characters")
        return v

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v: str) -> str:
        """
        Validate MIME type - must be in our allowed list.
        """
        mime_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9\-\+\.]*\/[a-zA-Z0-9][a-zA-Z0-9\-\+\.]*$"

        if not re.match(mime_pattern, v):
            raise ValueError("Invalid MIME type format")

        content_type_base = v.lower().split(";")[0].strip()

        if content_type_base not in cls.ALLOWED_CONTENT_TYPES:
            allowed_sample = list(cls.ALLOWED_CONTENT_TYPES.keys())[:5]
            raise ValueError(
                f"Content type '{content_type_base}' is not supported. "
                f"Examples of allowed types: {', '.join(allowed_sample)}..."
            )

        return content_type_base

    @model_validator(mode="after")
    def validate_consistency(self) -> "FileUploadRequest":
        """
        Ensure file extension and content type are consistent.
        """
        file_ext = "." + self.filename.split(".")[-1].lower()

        allowed_extensions = [ext.lower() for ext in self.ALLOWED_CONTENT_TYPES.get(self.content_type, [])]
        ext_to_types = self.get_extension_to_content_types()
        valid_content_types = ext_to_types.get(file_ext, [])

        if file_ext not in allowed_extensions and self.content_type not in valid_content_types:
            raise ValueError(
                f"File extension '{file_ext}' doesn't match content type '{self.content_type}'. "
                f"Valid content types for '{file_ext}': {', '.join(valid_content_types)}"
            )

        return self
