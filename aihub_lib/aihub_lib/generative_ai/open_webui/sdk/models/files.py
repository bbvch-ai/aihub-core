from typing import Annotated, Any

from pydantic import BaseModel, Field


class FileMeta(BaseModel):
    """Metadata about a file including format, size, and optional custom data."""

    name: Annotated[str | None, Field(description="Display name of the file")] = None
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None
    size: Annotated[int | None, Field(description="File size in bytes")] = None
    data: Annotated[dict[str, Any] | None, Field(description="Custom metadata")] = None

    model_config = {"extra": "allow"}


class FileModel(BaseModel):
    """
    Complete model representing a file in the OpenWebUI system.
    Contains all file metadata, content references, and access control information.
    """

    id: Annotated[str, Field(description="Unique file identifier")]
    user_id: Annotated[str, Field(description="ID of the user who owns the file")]
    hash: Annotated[str | None, Field(description="File content hash")] = None

    filename: Annotated[str, Field(description="Original filename")]
    path: Annotated[str | None, Field(description="Storage path")] = None

    data: Annotated[dict[str, Any] | None, Field(description="File content data")] = None
    meta: Annotated[dict[str, Any] | None, Field(description="File metadata")] = None

    access_control: Annotated[dict[str, Any] | None, Field(description="Access control settings")] = None

    created_at: Annotated[int, Field(description="Creation timestamp (epoch)")]
    updated_at: Annotated[int, Field(description="Last update timestamp (epoch)")]


class FileModelResponse(BaseModel):
    """Response model returned by file API endpoints."""

    id: Annotated[str, Field(description="Unique file identifier")]
    user_id: Annotated[str, Field(description="ID of the user who owns the file")]
    hash: Annotated[str | None, Field(description="File content hash")] = None

    filename: Annotated[str, Field(description="Original filename")]
    data: Annotated[dict[str, Any] | None, Field(description="File content data")] = None
    meta: Annotated[FileMeta, Field(description="File metadata")]

    created_at: Annotated[int, Field(description="Creation timestamp (epoch)")]
    updated_at: Annotated[int, Field(description="Last update timestamp (epoch)")]

    error: Annotated[str | None, Field(description="Error message if processing failed")] = None

    model_config = {"extra": "allow"}


class FileMetadataResponse(BaseModel):
    """Response model with only file metadata, used for lightweight queries."""

    id: Annotated[str, Field(description="Unique file identifier")]
    meta: Annotated[dict[str, Any], Field(description="File metadata")]
    created_at: Annotated[int, Field(description="Creation timestamp (epoch)")]
    updated_at: Annotated[int, Field(description="Last update timestamp (epoch)")]


class FileForm(BaseModel):
    """Form data for creating a new file."""

    id: Annotated[str, Field(description="Unique file identifier")]
    hash: Annotated[str | None, Field(description="File content hash")] = None
    filename: Annotated[str, Field(description="Original filename")]
    path: Annotated[str, Field(description="Storage path")]
    data: Annotated[dict[str, Any], Field(description="File content data")] = {}
    meta: Annotated[dict[str, Any], Field(description="File metadata")] = {}
    access_control: Annotated[dict[str, Any] | None, Field(description="Access control settings")] = None


class ContentForm(BaseModel):
    """Form data for updating file content."""

    content: Annotated[str, Field(description="New file content")]


class ProcessFileForm(BaseModel):
    """Form data for processing a file."""

    file_id: Annotated[str, Field(description="ID of the file to process")]
    content: Annotated[str | None, Field(description="Optional content to use instead of file content")] = None
