import httpx
from azure.identity import DefaultAzureCredential

from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.routes.user.dto.UserDTO import UserDTO


class AzureUserInformationProvider(BaseUserInformationProvider):
    """
    A user information provider that uses Microsoft Graph and Azure credentials.

    ### Why This Class?
    In Azure-based environments, user information often comes from Microsoft Graph.
    `AzureUserInformationProvider` leverages `DefaultAzureCredential` to:
    - Automatically handle token acquisition (using Managed Identity in Azure or developer credentials locally).
    - Query Microsoft Graph's `/users/{oid}` endpoint to fetch user profile details.

    ### How It Works
    1. Initialize `DefaultAzureCredential`, which attempts multiple credentials (Managed Identity, VS Code auth,
       Azure CLI, etc.) to find a suitable token.
    2. Request a token for the Microsoft Graph scope (`https://graph.microsoft.com/.default`).
    3. Use this token to call Microsoft Graph and retrieve the user's displayName, email, etc.

    This prints the user's display name and email fetched from Microsoft Graph.
    """

    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.scope = "https://graph.microsoft.com/.default"

    def get_user_info_by_oid(self, oid: str) -> UserDTO:
        """
        Fetch user information from Microsoft Graph using an OID.

        :param oid: The unique OID of the user in Azure AD.
        :return: A `UserDTO` with user details like id, name, and email.
        :raises Exception: If the request to Microsoft Graph fails.
        """
        # Acquire an access token from Azure Identity
        access_token = self.credential.get_token(self.scope).token

        url = f"https://graph.microsoft.com/v1.0/users/{oid}"
        headers = {"Authorization": f"Bearer {access_token}"}

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
            raise Exception(f"Failed to fetch user info. Status: {response.status_code}, Response: {response.text}")
