import asyncio
import base64
import logging
from typing import Any

import httpx
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from cachetools import TTLCache

from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class GraphAPIError(Exception):
    """Custom exception for errors during Microsoft Graph API calls."""

    def __init__(self, message: str, status_code: int | None = None, response_text: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

    def __str__(self):
        return f"{super().__str__()} [Status Code: {self.status_code}]"


class AzureGraphService:
    """
    A service class for interacting with the Microsoft Graph API.

    This class provides production-ready, cached methods to fetch user identity,
    roles, and profile information from Azure Active Directory. It follows a
    fail-fast philosophy, raising GraphAPIError for unexpected API failures.
    """

    MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self, client_id: str, default_ttl: int = 3600):
        self.client_id = client_id
        self.credential = AsyncDefaultAzureCredential()
        self.graph_scope = "https://graph.microsoft.com/.default"

        # Consolidated and configurable caching
        self.user_profile_cache = TTLCache(maxsize=128, ttl=default_ttl)
        self.profile_image_cache = TTLCache(maxsize=128, ttl=default_ttl * 5)  # Images change less often
        self.service_principal_cache = TTLCache(maxsize=64, ttl=default_ttl)
        self.app_role_assignments_cache = TTLCache(maxsize=128, ttl=600)  # Assignments can change more frequently

    async def _get_token(self) -> str:
        """Acquires an OAuth2 token for the Microsoft Graph API."""
        logger.debug("Attempting to get Graph API token.")
        try:
            token_result = await self.credential.get_token(self.graph_scope)
            logger.debug(f"Token acquired, expires on: {token_result.expires_on}")
            return token_result.token
        except Exception as e:
            logger.exception("Failed to acquire Graph API token.")
            raise GraphAPIError("Failed to acquire Graph API token.") from e

    async def _make_graph_request(
        self,
        method: str,
        url: str,
        access_token: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        A centralized helper for making authorized requests to the Graph API.
        Handles token acquisition, header injection, and robust error handling.
        """
        token = access_token or await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "ConsistencyLevel": "eventual",  # Needed for some filter queries
            **kwargs.pop("headers", {}),
        }

        # Increased connect timeout to 30s to allow IPv6 failures to fall back to IPv4
        timeout = httpx.Timeout(30.0, connect=30.0, read=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(method, url, headers=headers, **kwargs)

        if "application/json" not in response.headers.get("Content-Type", ""):
            if response.status_code == 200:
                return {"content": response.content, "headers": response.headers}
            if response.status_code == 404:
                return {}  # Return empty dict for not found, lets caller decide if its an error

        # For JSON responses, check status and raise on failure
        if response.status_code not in {200, 201, 204}:
            raise GraphAPIError(
                f"Graph API request to {url} failed.",
                status_code=response.status_code,
                response_text=response.text,
            )

        return response.json() if response.status_code != 204 else {}

    async def _get_user_profile(self, user_oid: str) -> dict[str, Any]:
        """
        Fetches a user's core profile from Graph API by their Object ID.
        Returns the raw user data dictionary on success.
        """
        cache_key = f"user_profile_{user_oid}"
        if cache_key in self.user_profile_cache:
            logger.debug(f"Cache hit for user_profile_{user_oid}.")
            return self.user_profile_cache[cache_key]

        logger.debug(f"Fetching user profile for OID {user_oid}.")
        user_url = f"{self.MS_GRAPH_BASE_URL}/users/{user_oid}?$select=id,displayName,mail,userPrincipalName"

        try:
            user_data = await self._make_graph_request("GET", user_url)
        except GraphAPIError as e:
            if e.status_code == 404:
                raise ValueError(f"User not found for OID {user_oid}.") from e
            raise

        self.user_profile_cache[cache_key] = user_data
        return user_data

    async def _get_user_profile_by_email(self, email: str) -> dict[str, Any]:
        """Finds a user's OID by email and fetches their profile."""
        logger.debug(f"Fetching user by email {email}.")
        # Use a filter that works for both mail and UPN
        search_url = (
            f"{self.MS_GRAPH_BASE_URL}/users?$filter=mail eq '{email}' or userPrincipalName eq '{email}'&$select=id"
        )

        response_data = await self._make_graph_request("GET", search_url)
        users = response_data.get("value", [])

        if not users:
            raise ValueError(f"User not found for email {email}.")
        if len(users) > 1:
            raise ValueError(f"Multiple users found for email {email}.")

        user_oid = users[0]["id"]
        logger.debug(f"User found by email {email}: OID {user_oid}")
        return await self._get_user_profile(user_oid)

    async def get_user_profile_image_data_url(self, user_oid: str) -> str | None:
        """
        Fetches a user's profile photo and returns it as a base64 data URL.
        Returns None if the user has no photo (404), raises on other errors.
        """
        cache_key = f"profile_image_{user_oid}"
        if cache_key in self.profile_image_cache:
            logger.debug(f"Cache hit for profile_image_{user_oid}.")
            return self.profile_image_cache[cache_key]

        logger.debug(f"Fetching profile image for user OID {user_oid}.")
        image_url = f"{self.MS_GRAPH_BASE_URL}/users/{user_oid}/photo/$value"
        try:
            image_response = await self._make_graph_request("GET", image_url)
        except GraphAPIError as e:
            if e.status_code != 404:
                logger.warning(f"Unable to fetch user profile image: {e}")
            return None

        if not image_response:
            return None

        content_type = image_response["headers"].get("Content-Type", "image/jpeg")
        base64_data = base64.b64encode(image_response["content"]).decode("utf-8")
        image_data_url = f"data:{content_type};base64,{base64_data}"

        self.profile_image_cache[cache_key] = image_data_url
        return image_data_url

    async def get_user_roles(self, user_oid: str) -> list[str]:
        """
        Calculates the effective application roles for a user for this specific application.
        """
        # 1. Get the Service Principal of our own application
        sp_cache_key = f"service_principal_app_id_{self.client_id}"
        if sp_cache_key in self.service_principal_cache:
            app_sp_data = self.service_principal_cache[sp_cache_key]
        else:
            sp_url = f"{self.MS_GRAPH_BASE_URL}/servicePrincipals?$filter=appId eq '{self.client_id}'"
            sp_response = await self._make_graph_request("GET", sp_url)
            principals = sp_response.get("value", [])
            app_sp_data = principals[0] if principals else None
            self.service_principal_cache[sp_cache_key] = app_sp_data

        if not app_sp_data or not app_sp_data.get("id"):
            logger.warning(
                f"Could not find Service Principal for app client_id {self.client_id}. Cannot determine roles."
            )
            return []

        # 2. Map role definitions from the Service Principal
        target_app_sp_id = app_sp_data["id"]
        app_role_definitions = {
            role["id"]: role["value"]
            for role in app_sp_data.get("appRoles", [])
            if role.get("isEnabled") and role.get("id") and role.get("value")
        }

        if not app_role_definitions:
            logger.info("No enabled app roles are defined on the application SP.")
            return []

        # 3. Get the user's role assignments for our application's SP
        assignments_cache_key = f"assignments_{user_oid}_for_sp_{target_app_sp_id}"
        if assignments_cache_key in self.app_role_assignments_cache:
            assigned_role_ids = self.app_role_assignments_cache[assignments_cache_key]
        else:
            assign_url = (
                f"{self.MS_GRAPH_BASE_URL}/users/{user_oid}/appRoleAssignments?"
                f"$filter=resourceId eq {target_app_sp_id}&$select=appRoleId"
            )
            assignments_response = await self._make_graph_request("GET", assign_url)
            assigned_role_ids = [a["appRoleId"] for a in assignments_response.get("value", [])]
            self.app_role_assignments_cache[assignments_cache_key] = assigned_role_ids

        # 4. Map the assigned IDs back to role names
        effective_roles = [
            app_role_definitions[role_id] for role_id in assigned_role_ids if role_id in app_role_definitions
        ]

        return sorted(list(set(effective_roles)))

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        """
        The primary method to build a complete UserIdentity object.
        It composes user profile, roles, and image from other methods.
        This is the preferred entry point for getting a user's full context.
        """
        logger.info(f"Building full UserIdentity for OID {user_oid} in context of app {self.client_id}.")

        # Concurrently fetch all pieces of information
        profile_task = self._get_user_profile(user_oid)
        roles_task = self.get_user_roles(user_oid)
        image_task = self.get_user_profile_image_data_url(user_oid)

        user_profile, user_roles, profile_image = await asyncio.gather(profile_task, roles_task, image_task)

        if not user_profile:
            raise ValueError(f"Could not construct UserIdentity, profile not found for OID {user_oid}.")

        return UserIdentity(
            id=user_oid,
            name=user_profile.get("displayName"),
            email=user_profile.get("mail") or user_profile.get("userPrincipalName"),
            roles=user_roles,
            profile_image=profile_image,
        )

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        """Convenience method to get a user's identity by their email."""
        user_profile = await self._get_user_profile_by_email(email)
        return await self.get_user_identity_by_oid(user_profile["id"])
