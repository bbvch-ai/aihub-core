from typing import Annotated, Any, Dict, Optional

from pydantic import BaseModel, Field


class UserUISettings(BaseModel):
    """
    Settings for the user interface with optional parameters and notifications.
    """

    params: Annotated[Dict[str, Any], Field(description="UI parameters")] = {}
    version: Annotated[Optional[str], Field(default=None, description="UI version")] = None
    notifications: Annotated[Optional[Dict[str, Any]], Field(default=None, description="Notification settings")] = None


class UserSettings(BaseModel):
    """
    User settings container that includes UI-specific settings.
    """

    ui: Annotated[UserUISettings, Field(default_factory=UserUISettings, description="UI settings")] = UserUISettings()


class User(BaseModel):
    """
    Represents a user in the OpenWebUI system with all associated metadata.

    Contains user identity, role, activity timestamps, and configurable settings.

    Example:
        ```python
        user = User(
            id="123",
            name="John Doe",
            email="john@example.com",
            role="user",
            profile_image_url="/user.png",
            last_active_at=1644039765,
            updated_at=1644039765,
            created_at=1644039765
        )
        ```
    """

    id: Annotated[str, Field(description="Unique user identifier")]
    name: Annotated[str, Field(description="Display name of the user")]
    email: Annotated[str, Field(description="Email address")]
    role: Annotated[str, Field(description="User role (admin, user, pending)")] = "user"
    profile_image_url: Annotated[str, Field(description="Profile image URL")]

    last_active_at: Annotated[int, Field(description="Last activity timestamp")]
    updated_at: Annotated[int, Field(description="Last update timestamp")]
    created_at: Annotated[int, Field(description="Creation timestamp")]

    api_key: Annotated[Optional[str], Field(default=None, description="API key for authentication")] = None
    settings: Annotated[UserSettings, Field(default_factory=UserSettings, description="User settings")] = UserSettings()
    info: Annotated[Optional[Dict[str, Any]], Field(default=None, description="Additional user information")] = None
    oauth_sub: Annotated[Optional[str], Field(default=None, description="OAuth subject identifier")] = None


class UserUpdateRequest(BaseModel):
    """Data required to update a user's profile information."""

    name: Annotated[str, Field(description="New display name")]
    email: Annotated[str, Field(description="New email address")]
    profile_image_url: Annotated[str, Field(description="New profile image URL")]
    password: Annotated[Optional[str], Field(default=None, description="New password (optional)")] = None


class UserRoleUpdateRequest(BaseModel):
    """Data required to update a user's role."""

    id: Annotated[str, Field(description="User ID to update")]
    role: Annotated[str, Field(description="New role value")]


class UserResponse(BaseModel):
    """Basic user information returned by user lookup endpoints."""

    name: Annotated[str, Field(description="User display name")]
    profile_image_url: Annotated[str, Field(description="Profile image URL")]
    active: Annotated[Optional[bool], Field(default=None, description="Whether user is currently active")] = None


class ApiKeyResponse(BaseModel):
    """Response containing an API key."""

    api_key: Annotated[str, Field(description="The API key value")]


# Permission models
class WorkspacePermissions(BaseModel):
    """Permissions for workspace features."""

    models: Annotated[bool, Field(default=False, description="Can access models")] = False
    knowledge: Annotated[bool, Field(default=False, description="Can access knowledge base")] = False
    prompts: Annotated[bool, Field(default=False, description="Can access prompts")] = False
    tools: Annotated[bool, Field(default=False, description="Can access tools")] = False


class SharingPermissions(BaseModel):
    """Permissions for sharing content publicly."""

    public_models: Annotated[bool, Field(default=True, description="Can share models publicly")] = True
    public_knowledge: Annotated[bool, Field(default=True, description="Can share knowledge publicly")] = True
    public_prompts: Annotated[bool, Field(default=True, description="Can share prompts publicly")] = True
    public_tools: Annotated[bool, Field(default=True, description="Can share tools publicly")] = True


class ChatPermissions(BaseModel):
    """Permissions for chat functionality."""

    controls: Annotated[bool, Field(default=True, description="Can use chat controls")] = True
    file_upload: Annotated[bool, Field(default=True, description="Can upload files in chat")] = True
    delete: Annotated[bool, Field(default=True, description="Can delete chat messages")] = True
    edit: Annotated[bool, Field(default=True, description="Can edit chat messages")] = True
    temporary: Annotated[bool, Field(default=True, description="Can create temporary chats")] = True
    temporary_enforced: Annotated[bool, Field(default=False, description="Must use temporary chats")] = False


class FeaturesPermissions(BaseModel):
    """Permissions for additional features."""

    direct_tool_servers: Annotated[bool, Field(default=False, description="Can use direct tool servers")] = False
    web_search: Annotated[bool, Field(default=True, description="Can use web search")] = True
    image_generation: Annotated[bool, Field(default=True, description="Can use image generation")] = True
    code_interpreter: Annotated[bool, Field(default=True, description="Can use code interpreter")] = True


class UserPermissions(BaseModel):
    """Complete set of user permissions controlling access to different features."""

    workspace: Annotated[
        WorkspacePermissions, Field(default_factory=WorkspacePermissions, description="Workspace permissions")
    ] = WorkspacePermissions()
    sharing: Annotated[
        SharingPermissions, Field(default_factory=SharingPermissions, description="Sharing permissions")
    ] = SharingPermissions()
    chat: Annotated[ChatPermissions, Field(default_factory=ChatPermissions, description="Chat permissions")] = (
        ChatPermissions()
    )
    features: Annotated[
        FeaturesPermissions, Field(default_factory=FeaturesPermissions, description="Feature permissions")
    ] = FeaturesPermissions()
