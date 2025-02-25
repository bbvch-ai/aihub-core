import base64

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
        # Acquire an access token from Azure Identity
        access_token = self.credential.get_token(self.scope).token
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get basic user details
        user_url = f"https://graph.microsoft.com/v1.0/users/{oid}"
        with httpx.Client() as client:
            response = client.get(user_url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch user info. Status: {response.status_code}, Response: {response.text}")
        user_data = response.json()

        # Retrieve the profile image
        image_url = f"https://graph.microsoft.com/v1.0/users/{oid}/photo/$value"
        with httpx.Client() as client:
            image_response = client.get(image_url, headers=headers)

        if image_response.status_code == 200:
            image_content = image_response.content
            # Determine the MIME type from the response, defaulting to image/jpeg
            content_type = image_response.headers.get("Content-Type", "image/jpeg")
            # Encode image and prepend with the data URI scheme
            base64_data = base64.b64encode(image_content).decode("utf-8")
            data_url = f"data:{content_type};base64,{base64_data}"
        else:
            data_url = None

        # Return user information with the base64 encoded profile image as a data URI
        return UserDTO(
            id=user_data.get("id"),
            name=user_data.get("displayName"),
            email=user_data.get("mail") or user_data.get("userPrincipalName"),
            profile_image=data_url,  # Ensure your UserDTO accepts this field.
        )
