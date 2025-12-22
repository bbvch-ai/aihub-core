import logging

from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Settings import OAuth2Settings
from aihub_lib.auth.identity.AzureIdentityProvider.AzureGraphService import AzureGraphService
from aihub_lib.auth.identity.IdentityProvider import IdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)


class AzureIdentityProvider(IdentityProvider):
    """
    Provides user information (profile, image) by querying Microsoft Graph.

    Roles are NO LONGER fetched from the identity provider. Role management
    is handled locally through the multi-tenant system (UserTenantRoleEntity).
    """

    def __init__(self):
        self.config = OAuth2Settings()
        self.graph_service = AzureGraphService(self.config.CLIENT_ID)

    async def get_user_identity_by_oid(self, user_oid: str) -> UserIdentity:
        """
        Retrieves user identity from Azure AD and ensures the user exists locally.

        Roles are resolved from the local database, not from Azure AD.
        New users are automatically assigned to the default tenant with default roles.
        """
        graph_identity = await self.graph_service.get_user_identity_by_oid(user_oid)

        user_entity = UserEntity.ensure_user_exists_for_auth(
            oid=graph_identity.id,
            name=graph_identity.name,
            email=graph_identity.email,
            profile_image=graph_identity.profile_image,
        )

        return UserIdentity(
            id=user_entity.id,
            name=user_entity.name,
            email=user_entity.email,
            roles=user_entity.roles,
            profile_image=user_entity.profile_image,
        )

    async def get_user_identity_by_email(self, email: str) -> UserIdentity:
        graph_identity = await self.graph_service.get_user_identity_by_email(email)
        return await self.get_user_identity_by_oid(graph_identity.id)

    async def get_user_roles(self, user_oid: str) -> list[str]:
        """Returns roles from the local database, not from the identity provider."""
        user = UserEntity.by_oid(user_oid)
        return user.roles if user else []

    async def get_user_profile_image_data_url(self, user_oid: str) -> str | None:
        return await self.graph_service.get_user_profile_image_data_url(user_oid)
