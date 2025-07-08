import logging
from typing import List, Optional

from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config
from aihub_lib.auth.identity.AzureIdentityProvider.AzureGraphService import AzureGraphService
from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)


class AzureIdentityProvider(IdentityProvider):
    """
    Provides user information (profile, image, app-specific roles) by querying Microsoft Graph.
    The application context for roles is defined by CLIENT_ID in OAuth2Config.
    """

    def __init__(self):
        self.config = OAuth2Config()
        self.graph_service = AzureGraphService(self.config.CLIENT_ID)

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        user_identity = await self.graph_service.get_user_identity_by_oid(user_oid)
        UserEntity.ensure_user_exists(
            oid=user_identity.id,
            name=user_identity.name,
            email=user_identity.email,
            roles=user_identity.roles,
            profile_image=user_identity.profile_image,
        )
        return user_identity

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        return await self.graph_service.get_user_identity_by_email(email)

    async def get_user_roles(self, user_oid: str) -> List[str]:
        return await self.graph_service.get_user_roles(user_oid)

    async def get_user_profile_image_data_url(self, user_oid: str) -> Optional[str]:
        return await self.graph_service.get_user_profile_image_data_url(user_oid)
