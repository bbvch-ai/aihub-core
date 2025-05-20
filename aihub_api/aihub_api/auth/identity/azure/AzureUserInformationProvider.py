import logging
from typing import Optional

from aihub_lib.auth.azure_graph.AzureGraphService import AzureGraphService
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config

from aihub_api.auth.identity.BaseUserInformationProvider import BaseUserInformationProvider
from aihub_api.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class AzureUserInformationProvider(BaseUserInformationProvider):
    """
    Provides user information (profile, image, app-specific roles) by querying Microsoft Graph.
    The application context for roles is defined by CLIENT_ID in OAuth2Config.
    """

    def __init__(self):
        self.graph_service = AzureGraphService()
        self.config = OAuth2Config()
        self.app_client_id_for_roles: Optional[str] = self.config.CLIENT_ID

    async def get_user_info_by_oid(self, oid: str) -> UserIdentity:
        """
        Acquires a token and retrieves user data (profile, image, app-specific roles) by OID.
        """
        logger.debug(
            f"AzureUserInformationProvider: Getting user info for OID: {oid} using app client_id {self.app_client_id_for_roles} for roles."
        )

        user_app_details = await self.graph_service.get_user_details_for_app_context(
            user_oid=oid, app_client_id_for_roles=self.app_client_id_for_roles
        )

        profile = user_app_details.get("profile")

        if not profile:
            raise ValueError(f"AzureUserInformationProvider: No profile found for OID: {oid}.")

        profile_id = profile.get("id")
        name = profile.get("displayName")
        email = profile.get("mail") or profile.get("userPrincipalName")
        profile_image = user_app_details.get("image_url")
        roles = user_app_details.get("app_roles", [])

        if not all([profile_id, name, email]):
            raise ValueError(f"AzureUserInformationProvider: Missing profile data for OID: {oid}.")

        return UserIdentity(
            id=profile_id,
            name=name,
            email=email,
            profile_image=profile_image,
            roles=roles,
        )
