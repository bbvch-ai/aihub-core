import logging

from fastapi import Request

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

logger = logging.getLogger(__name__)


class DangerousDevelopmentOnlyAuthHandler(AuthHandler):
    """
    A FastAPI dependency for development/testing only.

    Bypasses all authentication and returns a fake user identity from configuration.
    WARNING: Never use in production!
    """

    def __init__(self) -> None:
        self.config = DangerousDevelopmentOnlyAuthSettings()

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        """
        Returns fake dev user identity - no actual authentication.

        Ensures the dev user has tenant roles and an active tenant set.
        """
        logger.warning("DangerousDevelopmentOnlyAuthHandler is active. This is not recommended for production use.")

        default_tenant = TenantMetadataEntity.get_default_tenant_metadata()
        if default_tenant:
            UserTenantRoleEntity.create_or_update(
                user_id=self.config.OID,
                tenant_id=str(default_tenant.id),
                roles=self.config.ROLES,
                validate_roles=False,
            )
            # Ensure active tenant is set
            active_tenant_id = await KeycloakAdminService.get_active_tenant_id(self.config.OID)
            if not active_tenant_id:
                await KeycloakAdminService.set_active_tenant(self.config.OID, str(default_tenant.id))
        return await self.build_identity(
            user_id=self.config.OID, name=self.config.NAME, email=self.config.EMAIL, request=request
        )
