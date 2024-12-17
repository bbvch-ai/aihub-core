import httpx
from azure.identity import DefaultAzureCredential

from api_core.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider

import msal

from api_core.routes.user.dto.UserDTO import UserDTO


class AzureUserInformationProvider(BaseUserInformationProvider):
    """
    A Microsoft-specific implementation of the user information provider that uses
    DefaultAzureCredential to obtain tokens for Microsoft Graph. This approach works well
    when running in Azure with Managed Identities or in development environments supported by
    the DefaultAzureCredential chain.
    """

    def __init__(self):
        # Initialize the default credential. In Azure, this will use Managed Identity if available.
        self.credential = DefaultAzureCredential()
        self.scope = "https://graph.microsoft.com/.default"

    def get_user_info_by_oid(self, oid: str) -> dict:
        """
        Fetch user information (like name, email) from Microsoft Graph given a user OID.
        Uses DefaultAzureCredential to obtain a token for Microsoft Graph.
        """
        # Acquire an access token from Azure Identity
        access_token = self.credential.get_token(self.scope).token

        # Microsoft Graph endpoint for a specific user by their id (OID)
        url = f"https://graph.microsoft.com/v1.0/users/{oid}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        with httpx.Client() as client:
            response = client.get(url, headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            return UserDTO(
                id=user_data.get("id"),
                name=user_data.get("displayName"),
                email=user_data.get("mail") or user_data.get("userPrincipalName"),
            )
        else:
            raise Exception(
                f"Failed to fetch user info. Status: {response.status_code}, Response: {response.text}"
            )
