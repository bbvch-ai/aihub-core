from typing import Annotated

from pydantic import BaseModel, Field


class MinimalSourceFile(BaseModel):
    """
    Minimal base model for source file metadata without content.

    This lightweight base model is used when only metadata is needed (e.g., for
    comparing source files with data lake files to determine which files to remove).
    It excludes the potentially large file content to improve performance when
    processing large numbers of files.

    This is commonly used by observable assets that scan source systems for changes
    without downloading full file contents.
    """

    name: Annotated[str, Field(description="File name including extension")]
    path: Annotated[str, Field(description="Relative path within the source system")]
    size: Annotated[int, Field(description="File size in bytes")]
    modified: Annotated[int, Field(description="The UNIX timestamp when the file was last modified")]


class SourceFile(MinimalSourceFile):
    """
    Generic base model for files from any source system.

    This base model defines the common interface that all source file types
    (SharePoint, local file system, cloud storage, etc.) should extend. It ensures
    that downstream pipeline operations can work with files from any source without
    needing source-specific logic.

    The interface provides access to:
    - File content and metadata (name, path, size)
    - Temporal information (created, modified timestamps as Unix timestamps)
    - Source origin information (URL or path in the source system)

    Example implementations:
        - SharePointFile: Files retrieved from Microsoft SharePoint
        - S3File: Files from AWS S3 buckets
    """

    content: Annotated[bytes, Field(description="File content as bytes")]
    created: Annotated[int, Field(description="The UNIX timestamp when the file was created")]
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None

    @property
    def source_url(self) -> str:
        """
        Full URL or path in the source system.

        Subclasses should override this to provide the appropriate source URL.
        """
        return self.path
