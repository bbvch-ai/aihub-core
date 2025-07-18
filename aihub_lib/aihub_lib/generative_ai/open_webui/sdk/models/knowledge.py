from typing import Annotated, Any

from pydantic import BaseModel, Field

from .files import FileMetadataResponse, FileModel


class UserResponse(BaseModel):
    """Basic user information included in knowledge base responses."""

    id: Annotated[str, Field(description="User identifier")]
    name: Annotated[str, Field(description="User display name")]
    profile_image_url: Annotated[str, Field(description="Profile image URL")]
    role: Annotated[str, Field(description="User role")]


class KnowledgeAccessControlPermissions(BaseModel):
    """Access control permissions for a specific operation (read or write)."""

    user_ids: Annotated[list[str], Field(description="List of user IDs with this permission")] = []
    group_ids: Annotated[list[str], Field(description="List of group IDs with this permission")] = []


class KnowledgeAccessControl(BaseModel):
    """
    Access control settings for a knowledge base.

    Controls who can read or write to the knowledge base.
    Empty lists mean no specific permissions (public for read, owner-only for write).
    """

    read: Annotated[
        KnowledgeAccessControlPermissions,
        Field(default_factory=KnowledgeAccessControlPermissions, description="Read permissions"),
    ] = KnowledgeAccessControlPermissions()
    write: Annotated[
        KnowledgeAccessControlPermissions,
        Field(default_factory=KnowledgeAccessControlPermissions, description="Write permissions"),
    ] = KnowledgeAccessControlPermissions()


class KnowledgeData(BaseModel):
    """
    Data associated with a knowledge base.

    Contains primarily the list of file IDs that are included in this knowledge base.
    Additional custom data can be included in the extra_data field.
    """

    file_ids: Annotated[list[str], Field(description="List of file IDs in this knowledge base")] = []
    extra_data: Annotated[dict[str, Any], Field(description="Any additional custom data")] = {}

    def model_dump(self) -> dict[str, Any]:
        """Convert to a flat dictionary for API consumption"""
        result = {"file_ids": self.file_ids}
        result.update(self.extra_data)
        return result


class KnowledgeModel(BaseModel):
    """
    Represents a knowledge base in OpenWebUI.

    Knowledge bases organize collections of files for retrieval and context.
    """

    id: Annotated[str, Field(description="Unique knowledge base identifier")]
    user_id: Annotated[str, Field(description="ID of the user who owns the knowledge base")]

    name: Annotated[str, Field(description="Name of the knowledge base")]
    description: Annotated[str, Field(description="Description of the knowledge base")]

    data: Annotated[KnowledgeData | None, Field(description="File IDs and other data")] = None
    meta: Annotated[dict[str, Any] | None, Field(description="Metadata about the knowledge base")] = None

    access_control: Annotated[KnowledgeAccessControl | None, Field(description="Access control settings")] = None

    created_at: Annotated[int, Field(description="Creation timestamp (epoch)")]
    updated_at: Annotated[int, Field(description="Last update timestamp (epoch)")]


class KnowledgeUserModel(KnowledgeModel):
    """Knowledge base with owner user information."""

    user: Annotated[UserResponse | None, Field(description="User who owns the knowledge base")] = None


class KnowledgeResponse(KnowledgeModel):
    """Knowledge base with associated files metadata."""

    files: Annotated[list[FileMetadataResponse] | None, Field(description="Associated files metadata")] = None


class KnowledgeUserResponse(KnowledgeUserModel):
    """Knowledge base with both owner information and files metadata."""

    files: Annotated[list[FileMetadataResponse] | None, Field(description="Associated files metadata")] = None


class KnowledgeFilesResponse(KnowledgeResponse):
    """Knowledge base with complete file information (not just metadata)."""

    files: Annotated[list[FileModel], Field(description="Associated files with full details")]


class KnowledgeForm(BaseModel):
    """Form data for creating or updating a knowledge base."""

    name: Annotated[str, Field(description="Name of the knowledge base")]
    description: Annotated[str, Field(description="Description of the knowledge base")]
    data: Annotated[KnowledgeData | dict[str, Any] | None, Field(description="File IDs and other data")] = None
    access_control: Annotated[
        KnowledgeAccessControl | dict[str, Any] | None,
        Field(description="Access control settings"),
    ] = None


class KnowledgeFileIdForm(BaseModel):
    """Form data for adding/removing a file to/from a knowledge base."""

    file_id: Annotated[str, Field(description="ID of the file to add or remove")]
