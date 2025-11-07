from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from aihub_pipeline.types.SourceFile import MinimalSourceFile, SourceFile


class MinimalLocalFile(BaseModel, MinimalSourceFile):
    """
    Minimal file metadata without content - used for scanning and versioning.

    This lightweight representation is used by observable assets that scan the local
    file system for changes without reading full file contents. It provides just enough
    metadata to detect changes and determine which files need to be processed.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: Annotated[str, Field(description="File name")]
    file_path: Annotated[str, Field(alias="path", description="Relative path to the file")]
    full_path: Annotated[str, Field(description="Absolute path to the file")]
    size: Annotated[int, Field(description="File size in bytes")]
    modified: Annotated[float, Field(description="Unix timestamp when file was last modified")]
    created: Annotated[float, Field(description="Unix timestamp when file was created")]
    source_folder: Annotated[str, Field(description="Source folder name")]
    subfolder: Annotated[str | None, Field(description="Subfolder name")] = None

    @property
    def path(self) -> str:
        """Relative path within the source system (implements MinimalSourceFile.path)."""
        return self.file_path

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

    model_config = ConfigDict(populate_by_name=True)

    file_path: Annotated[str, Field(alias="path", description="Relative path to the file")]
    file_content: Annotated[bytes, Field(alias="content", description="File content as bytes")]
    file_name: Annotated[str, Field(alias="name", description="File name")]
    file_size: Annotated[int, Field(alias="size", description="File size in bytes")]
    modified: Annotated[str, Field(description="ISO datetime string when file was last modified")]
    created: Annotated[str, Field(description="ISO datetime string when file was created")]
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None
    full_path: Annotated[str, Field(description="Absolute file system path")]
    source_folder: Annotated[str, Field(description="Source folder name")]
    subfolder: Annotated[str | None, Field(description="Subfolder name")] = None

    @property
    def path(self) -> str:
        """Relative path within the source system (implements SourceFile.path)."""
        return self.file_path

    @property
    def content(self) -> bytes:
        """File content as raw bytes (implements SourceFile.content)."""
        return self.file_content

    @property
    def name(self) -> str:
        """File name including extension (implements SourceFile.name)."""
        return self.file_name

    @property
    def size(self) -> int:
        """File size in bytes (implements SourceFile.size)."""
        return self.file_size

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
        """Returns the URL as the source URL with forward slashes."""
        from pathlib import Path

        return Path(self.full_path).as_posix()
