"""
Pydantic models for OpenWebUI SDK API interactions.
"""

from .files import ContentForm, FileForm, FileMeta, FileMetadataResponse, FileModel, FileModelResponse, ProcessFileForm
from .knowledge import (
    KnowledgeFileIdForm,
    KnowledgeFilesResponse,
    KnowledgeForm,
    KnowledgeModel,
    KnowledgeResponse,
    KnowledgeUserModel,
    KnowledgeUserResponse,
)
from .users import (
    ApiKeyResponse,
    ChatPermissions,
    FeaturesPermissions,
    SharingPermissions,
    User,
    UserPermissions,
    UserResponse,
    UserRoleUpdateRequest,
    UserSettings,
    UserUISettings,
    UserUpdateRequest,
    WorkspacePermissions,
)

__all__ = [
    # User models
    "User",
    "UserSettings",
    "UserUpdateRequest",
    "UserRoleUpdateRequest",
    "UserResponse",
    "ApiKeyResponse",
    "UserPermissions",
    "WorkspacePermissions",
    "SharingPermissions",
    "ChatPermissions",
    "FeaturesPermissions",
    "UserUISettings",
    # File models
    "FileModel",
    "FileModelResponse",
    "FileMetadataResponse",
    "FileMeta",
    "FileForm",
    "ContentForm",
    "ProcessFileForm",
    # Knowledge models
    "KnowledgeModel",
    "KnowledgeUserModel",
    "KnowledgeResponse",
    "KnowledgeUserResponse",
    "KnowledgeFilesResponse",
    "KnowledgeForm",
    "KnowledgeFileIdForm",
    "KnowledgeUserResponse",
]
