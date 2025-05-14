import base64
import httpx
from azure.identity import DefaultAzureCredential
from cachetools import TTLCache, cached

from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.auth.identity.UserIdentity import UserIdentity
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config

MS_GRAPH_V1_BASE_URL = "https://graph.microsoft.com/v1.0"

class AzureUserInformationProvider(BaseUserInformationProvider):
    """
    Provides user information by querying Microsoft Graph using Azure credentials.
    It fetches user profile details, profile picture, and application-specific roles.
    This version has minimal error handling and comments.
    """

    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.scope = "https://graph.microsoft.com/.default"

        self.config = OAuth2Config()
        self.client_id = self.config.CLIENT_ID

        self.app_service_principal_id: str | None = None
        self.app_role_definitions: dict[str, str] = {}

        if self.client_id:
            self._initialize_app_details()

    def _make_graph_api_request(
            self, method: str, url: str, client: httpx.Client, headers: dict, **kwargs
    ) -> httpx.Response:
        """Makes a Graph API request and raises an exception for HTTP errors."""
        response = client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    def _initialize_app_details(self):
        """
        Fetches the application's service principal ID and app role definitions.
        Raises exceptions on failure (e.g., token error, SP not found).
        """
        token_val = self.credential.get_token(self.scope).token

        headers = {"Authorization": f"Bearer {token_val}", "ConsistencyLevel": "eventual"}
        sp_url = f"{MS_GRAPH_V1_BASE_URL}/servicePrincipals?$filter=appId eq '{self.client_id}'&$select=id,appRoles"

        with httpx.Client() as client:
            response = self._make_graph_api_request("GET", sp_url, client, headers)
            data = response.json()

        value = data.get("value")
        if not value:
            raise ValueError(f"Service Principal not found for appId '{self.client_id}'.")

        sp_data = value[0]
        self.app_service_principal_id = sp_data.get("id")

        if not self.app_service_principal_id:
            raise ValueError(f"Service Principal ID is missing for appId '{self.client_id}'.")

        for role in sp_data.get("appRoles", []):
            if role.get("isEnabled"):
                role_id = role.get("id")
                role_identifier = role.get("value") or role.get("displayName")
                if role_id and role_identifier:
                    self.app_role_definitions[role_id] = role_identifier

    def _fetch_user_profile(self, client: httpx.Client, oid: str, headers: dict) -> dict:
        """Fetches basic user profile data. Raises exceptions on failure."""
        user_url = f"{MS_GRAPH_V1_BASE_URL}/users/{oid}?$select=id,displayName,mail,userPrincipalName"
        response = self._make_graph_api_request("GET", user_url, client, headers)
        return response.json()

    def _fetch_profile_image_data_url(self, client: httpx.Client, oid: str, headers: dict) -> str | None:
        """
        Fetches user profile image. Returns None if not found (404).
        Other HTTP errors will cause exceptions.
        """
        image_url = f"{MS_GRAPH_V1_BASE_URL}/users/{oid}/photo/$value"
        image_response = client.get(image_url, headers=headers)

        if image_response.status_code == 404:
            return None
        image_response.raise_for_status()

        image_content = image_response.content
        content_type = image_response.headers.get("Content-Type", "image/jpeg")
        base64_data = base64.b64encode(image_content).decode("utf-8")
        return f"data:{content_type};base64,{base64_data}"

    def _fetch_user_app_roles(self, client: httpx.Client, oid: str, headers: dict) -> list[str]:
        """
        Fetches user's app role assignments. Returns empty list if SP details are missing
        or if no assignments are found (404). Raises exceptions for other errors (e.g., 403).
        """
        if not self.app_service_principal_id or not self.app_role_definitions:
            return []

        assigned_roles: list[str] = []
        assignments_url = (
            f"{MS_GRAPH_V1_BASE_URL}/users/{oid}/appRoleAssignments"
            f"?$filter=resourceId eq {self.app_service_principal_id}"
            f"&$select=appRoleId"
        )

        response = client.get(assignments_url, headers=headers)

        if response.status_code == 404:
            return []
        response.raise_for_status()

        assignments = response.json().get("value", [])
        for assignment in assignments:
            app_role_id = assignment.get("appRoleId")
            role_value = self.app_role_definitions.get(app_role_id)
            if role_value:
                assigned_roles.append(role_value)
        return assigned_roles

    @cached(TTLCache(maxsize=128, ttl=60))
    def get_userdata_by_oid(self, oid: str, access_token: str) -> UserIdentity:
        """
        Retrieves user data, profile image, and roles based on OID and an access token.
        Caches the results. Lets exceptions from underlying calls propagate.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "ConsistencyLevel": "eventual"
        }

        with httpx.Client() as client:
            user_data_json = self._fetch_user_profile(client, oid, headers)
            profile_image_data_url = self._fetch_profile_image_data_url(client, oid, headers)
            role_names = self._fetch_user_app_roles(client, oid, headers)

        return UserIdentity(
            id=user_data_json.get("id"),
            name=user_data_json.get("displayName"),
            email=user_data_json.get("mail") or user_data_json.get("userPrincipalName"),
            profile_image=profile_image_data_url,
            roles=sorted(list(set(role_names))),
        )

    def get_user_info_by_oid(self, oid: str) -> UserIdentity:
        """
        Acquires an access token and retrieves user data by OID.
        Lets exceptions from token acquisition or data retrieval propagate.
        """
        access_token = self.credential.get_token(self.scope).token
        return self.get_userdata_by_oid(oid, access_token)