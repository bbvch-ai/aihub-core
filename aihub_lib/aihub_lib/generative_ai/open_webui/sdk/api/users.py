from typing import Any, Dict, List, Optional

from ..client import BaseClient
from ..models.users import (
    ApiKeyResponse,
    User,
    UserPermissions,
    UserResponse,
    UserRoleUpdateRequest,
    UserSettings,
    UserUpdateRequest,
)


class UsersClient(BaseClient):
    """
    Client for interacting with the OpenWebUI users API endpoints.

    Provides methods for managing users, including retrieving, creating,
    updating, and deleting users, as well as managing user permissions,
    settings, and API keys.

    Example:
        ```python
        from sdk import ApiClient

        client = ApiClient(token="your-token")
        # Get all users
        users = await client.users.get_users()

        # Update a user's role
        updated_user = await client.users.update_user_role(
            user_id="123",
            role="admin"
        )
        ```
    """

    async def get_users(self, skip: Optional[int] = None, limit: Optional[int] = None) -> List[User]:
        """Retrieve a list of all users with optional pagination"""
        params = {}
        if skip is not None:
            params["skip"] = skip
        if limit is not None:
            params["limit"] = limit

        response = await self.get("/api/v1/users/", params=params)
        return [User.model_validate(user) for user in response.json()]

    async def get_user_groups(self) -> List[Dict[str, Any]]:
        """Get groups for the authenticated user"""
        response = await self.get("/api/v1/users/groups")
        return response.json()

    async def get_user_permissions(self) -> Dict[str, Any]:
        """Get permissions for the authenticated user"""
        response = await self.get("/api/v1/users/permissions")
        return response.json()

    async def get_default_user_permissions(self) -> UserPermissions:
        """Get default user permissions (admin only)"""
        response = await self.get("/api/v1/users/default/permissions")
        return UserPermissions.model_validate(response.json())

    async def update_default_user_permissions(self, permissions: UserPermissions) -> Dict[str, Any]:
        """Update default user permissions (admin only)"""
        response = await self.post("/api/v1/users/default/permissions", json_data=permissions.model_dump())
        return response.json()

    async def update_user_role(self, user_id: str, role: str) -> Optional[User]:
        """Update a user's role (admin only)"""
        form_data = UserRoleUpdateRequest(id=user_id, role=role)
        response = await self.post("/api/v1/users/update/role", json_data=form_data.model_dump())
        if response.status_code == 200:
            return User.model_validate(response.json())
        return None

    async def get_user_settings(self) -> UserSettings:
        """Get settings for the authenticated user"""
        response = await self.get("/api/v1/users/user/settings")
        return UserSettings.model_validate(response.json())

    async def update_user_settings(self, settings: UserSettings) -> UserSettings:
        """Update settings for the authenticated user"""
        response = await self.post("/api/v1/users/user/settings/update", json_data=settings.model_dump())
        return UserSettings.model_validate(response.json())

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get additional info for the authenticated user"""
        response = await self.get("/api/v1/users/user/info")
        return response.json()

    async def update_user_info(self, info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update additional info for the authenticated user"""
        response = await self.post("/api/v1/users/user/info/update", json_data=info)
        return response.json()

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        """Get basic information about a user by ID"""
        response = await self.get(f"/api/v1/users/{user_id}")
        return UserResponse.model_validate(response.json())

    async def update_user(
        self, user_id: str, name: str, email: str, profile_image_url: str, password: Optional[str] = None
    ) -> Optional[User]:
        """Update a user's profile information (admin only)"""
        update_data = UserUpdateRequest(name=name, email=email, profile_image_url=profile_image_url, password=password)
        response = await self.post(f"/api/v1/users/{user_id}/update", json_data=update_data.model_dump())
        if response.status_code == 200:
            return User.model_validate(response.json())
        return None

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user by ID (admin only)"""
        response = await self.delete(f"/api/v1/users/{user_id}")
        return response.json()

    async def generate_api_key(self, user_id: str) -> ApiKeyResponse:
        """Generate a new API key for a user (admin only)"""
        response = await self.post(f"/api/v1/users/{user_id}/api_key", json_data={})
        return ApiKeyResponse.model_validate(response.json())

    async def get_api_key(self, user_id: str) -> ApiKeyResponse:
        """Get the API key for a user (admin only)"""
        response = await self.get(f"/api/v1/users/{user_id}/api_key")
        return ApiKeyResponse.model_validate(response.json())

    async def delete_api_key(self, user_id: str) -> bool:
        """Delete the API key for a user (admin only)"""
        response = await self.delete(f"/api/v1/users/{user_id}/api_key")
        return response.json()
