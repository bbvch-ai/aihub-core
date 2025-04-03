import hashlib
import logging

import httpx
from azure.identity import DefaultAzureCredential
from cachetools import TTLCache
from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.persistence.access.entities.BearerToken import BearerToken

logger = logging.getLogger(__name__)


def hash_string_sha1(input_string):
    static_salt = "k2oj3dk2*dk2p&29dkjklUdk(3kKldi39djkd?+lfdfdf"
    hash_input = f"{static_salt}{input_string}"
    input_bytes = hash_input.encode("utf-8")
    sha1_hash = hashlib.sha1(input_bytes)
    hex_digest = sha1_hash.hexdigest()
    return hex_digest


class OpenWebuiAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency that implements authentication for the open-webui frontend.

    This dependency expects the following headers to be present in the incoming request:
        - "X-OpenWebUI-User-Name": The user's full name.
        - "X-OpenWebUI-User-Id": The user's unique identifier.
        - "X-OpenWebUI-User-Email": The user's email address.
        - "X-OpenWebUI-User-Role": The user's role.

    The dependency extracts user information from these headers and maps it onto an `AuthenticatedUser`
    instance. If any of the required headers are missing or empty, an `HTTPException` with a 401 Unauthorized
    status is raised.

    Note:
        This authentication handler is intended for use exclusively with open-webui as the frontend.
    """

    def __init__(self):
        # Initialize Azure credential for Microsoft Graph access
        self.credential = DefaultAzureCredential()
        self.graph_scope = "https://graph.microsoft.com/.default"
        self.user_info_cache = TTLCache(maxsize=100, ttl=3600)  # Cache for user info

    async def get_user_by_email(self, email: str, access_token: str) -> AuthenticatedUser:
        """
        Retrieves user information from Microsoft Graph by email address,
        including roles assigned in enterprise applications.

        Args:
            email: The email address of the user to look up.

        Returns:
            A dictionary containing user information including OID and roles.
        """
        # Check if user info is cached
        if email in self.user_info_cache:
            logger.info(f"User info for {email} retrieved from cache.")
            return self.user_info_cache[email]

        # Get access token for Microsoft Graph
        headers = {"Authorization": f"Bearer {access_token}"}

        # Search for user by email using Microsoft Graph filter
        search_url = (
            f"https://graph.microsoft.com/v1.0/users?$filter=mail eq '{email}' or userPrincipalName eq '{email}'"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to query Microsoft Graph. Status: {response.status_code}, Response: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to resolve user identity")

        user_data = response.json()

        # Check if user was found
        if not user_data.get("value") or len(user_data["value"]) == 0:
            logger.warning(f"User with email {email} not found in Azure AD")
            raise HTTPException(status_code=401, detail="User not found in directory")

        user = user_data["value"][0]
        user_id = user["id"]
        user_roles = []

        # Get user's directory roles via memberOf
        roles_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf"
        async with httpx.AsyncClient() as client:
            roles_response = await client.get(roles_url, headers=headers)

        if roles_response.status_code == 200:
            roles_data = roles_response.json()
            # Extract directory roles
            for item in roles_data.get("value", []):
                if item.get("@odata.type", "").endswith("directoryRole"):
                    user_roles.append(item["displayName"])
        else:
            logger.warning(f"Failed to fetch directory roles. Status: {roles_response.status_code}")

        # Get user's app role assignments (roles assigned in enterprise applications)
        app_roles_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/appRoleAssignments"
        async with httpx.AsyncClient() as client:
            app_roles_response = await client.get(app_roles_url, headers=headers)

        if app_roles_response.status_code == 200:
            app_roles_data = app_roles_response.json()

            # Process each app role assignment
            for app_role in app_roles_data.get("value", []):
                # Get app details to find the role name
                app_id = app_role.get("resourceId")
                role_id = app_role.get("appRoleId")

                if app_id and role_id:
                    # Get service principal to find role names
                    sp_url = f"https://graph.microsoft.com/v1.0/servicePrincipals/{app_id}"
                    async with httpx.AsyncClient() as client:
                        sp_response = await client.get(sp_url, headers=headers)

                    if sp_response.status_code == 200:
                        sp_data = sp_response.json()
                        # Find the matching role definition
                        for role_def in sp_data.get("appRoles", []):
                            if role_def.get("id") == role_id:
                                user_roles.append(role_def.get("displayName"))
                                break
        else:
            logger.warning(f"Failed to fetch app role assignments. Status: {app_roles_response.status_code}")

        # Check if user is a member of security groups that may have role implications
        groups_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf?$filter=securityEnabled eq true"
        async with httpx.AsyncClient() as client:
            groups_response = await client.get(groups_url, headers=headers)

        if groups_response.status_code == 200:
            groups_data = groups_response.json()
            # Add security group memberships as roles - often used for RBAC
            for group in groups_data.get("value", []):
                if group.get("@odata.type", "").endswith("group"):
                    user_roles.append(f"Group_{group['displayName']}")
        else:
            logger.warning(f"Failed to fetch security groups. Status: {groups_response.status_code}")

        logger.info(f"Retrieved roles for user {email}: {user_roles}")

        user_info = AuthenticatedUser(
            name=user.get("displayName", ""),
            preferred_username=user.get("userPrincipalName", ""),
            oid=user["id"],
            roles=user_roles,
        )
        # Cache the user info
        self.user_info_cache[email] = user_info
        return user_info

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> AuthenticatedUser:
        token_str = bearer_token.credentials
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")

        try:
            access_token = BearerToken.verify_token(token_str)
        except ValueError as e:
            logger.warning("Token authentication failed: %s", e)
            raise HTTPException(status_code=401, detail=str(e))

        user_name = request.headers.get("X-OpenWebUI-User-Name")
        user_email = request.headers.get("X-OpenWebUI-User-Email")

        if not user_name or not user_email:
            # Fall back to token-based authentication if headers are missing
            return AuthenticatedUser(
                name=access_token.user.name,
                preferred_username=access_token.user.preferred_username,
                oid=access_token.user.oid,
                roles=access_token.roles,
            )

        user_name_hash = request.headers.get("X-OpenWebUI-User-Name-Hash")
        user_email_hash = request.headers.get("X-OpenWebUI-User-Email-Hash")

        if hash_string_sha1(user_name_hash) == user_email_hash or hash_string_sha1(user_email_hash) == user_name_hash:
            logger.warning("User name and email hashes do not match.")
            raise HTTPException(status_code=401, detail="User name and email hashes do not match.")

        # Resolve user information from Microsoft Graph using email
        access_token = self.credential.get_token(self.graph_scope).token
        return await self.get_user_by_email(user_email, access_token)

    async def authenticate_token(self, token_str: str) -> AuthenticatedUser:
        """
        Authenticates a user using a bearer token string directly.
        Used for WebSocket authentication.

        Note: For WebSocket connections, we don't have access to HTTP headers that would
        normally contain the X-OpenWebUI-* information. In this case, we rely solely on
        the information stored with the token.
        """
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")

        try:
            access_token = BearerToken.verify_token(token_str)
        except ValueError as e:
            logger.warning("Token authentication failed: %s", e)
            raise HTTPException(status_code=401, detail=str(e))

        api_user = access_token.user
        return AuthenticatedUser(
            name=api_user.name,
            preferred_username=api_user.preferred_username,
            oid=api_user.oid,
            roles=access_token.roles,
        )
