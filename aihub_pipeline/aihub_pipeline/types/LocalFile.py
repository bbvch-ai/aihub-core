from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from aihub_pipeline.types.SourceFile import MinimalSourceFile, SourceFile


class MinimalLocalFile(BaseModel, MinimalSourceFile):
    """
    Minimal file metadata without content - used for scanning and versioning.

    This lightweight representation is used by observable assets that scan the local
    file system for changes without reading full file contents. It provides just enough
    metadata to detect changes and determine which files need to be processed.
    """

    name: Annotated[str, Field(description="File name")]
    path: Annotated[str, Field(description="Relative path to the file")]
    full_path: Annotated[str, Field(description="Absolute path to the file")]
    size: Annotated[int, Field(description="File size in bytes")]
    modified: Annotated[float, Field(description="Unix timestamp when file was last modified")]
    created: Annotated[float, Field(description="Unix timestamp when file was created")]
    source_folder: Annotated[str, Field(description="Source folder name")]
    subfolder: Annotated[str | None, Field(description="Subfolder name")] = None

    @property
    def modified_datetime(self) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(self.modified)

    @property
    def created_datetime(self) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(self.created)


class LocalFile(BaseModel, SourceFile):
    """
    Local file system file implementation of the SourceFile interface.

    Represents a file from the local or network file system, including content,
    metadata, and file system-specific attributes like absolute paths and folder structure.
    """

    path: Annotated[str, Field(description="Relative path to the file")]
    content: Annotated[bytes, Field(description="File content as bytes")]
    name: Annotated[str, Field(description="File name")]
    size: Annotated[int, Field(description="File size in bytes")]
    modified: Annotated[str, Field(description="ISO datetime string when file was last modified")]
    created: Annotated[str, Field(description="ISO datetime string when file was created")]
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None
    full_path: Annotated[str, Field(description="Absolute file system path")]
    source_folder: Annotated[str, Field(description="Source folder name")]
    subfolder: Annotated[str | None, Field(description="Subfolder name")] = None

    @property
    def modified_datetime(self) -> datetime:
        """Parse ISO datetime string to datetime object."""
        return datetime.fromisoformat(self.modified.replace("Z", "+00:00"))

    @property
    def created_datetime(self) -> datetime:
        """Parse ISO datetime string to datetime object."""
        return datetime.fromisoformat(self.created.replace("Z", "+00:00"))

    @property
    def source_url(self) -> str:
        """Returns the file:// URL as the source URL."""
        return f"file://{self.full_path}"
