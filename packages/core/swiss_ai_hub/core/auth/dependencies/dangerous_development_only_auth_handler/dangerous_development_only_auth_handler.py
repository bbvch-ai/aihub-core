import logging

from fastapi import Request

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity

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

        Creates/updates the dev user in the database to ensure it exists for other parts of the codebase.
        The dev user is assigned roles from the DangerousDevelopmentOnlyAuthSettings config.
        """
        logger.warning("DangerousDevelopmentOnlyAuthHandler is active. This is not recommended for production use.")

        # Use ensure_user_exists (not ensure_user_exists_for_auth) because the dev handler
        # manages tenant roles separately with validate_roles=False for dev-only roles.
        user_entity = UserEntity.ensure_user_exists(
            oid=self.config.OID,
            name=self.config.NAME,
            email=self.config.EMAIL,
        )

        # Ensure the dev user has the roles from config in the default tenant
        default_tenant = TenantEntity.get_default_tenant()
        if default_tenant:
            UserTenantRoleEntity.create_or_update(
                user_id=user_entity.id,
                tenant_id=str(default_tenant.id),
                roles=self.config.ROLES,
                validate_roles=False,  # Dev roles may not exist in DB
            )

        # Resolve tenant context from request or use default
        if request and self.has_tenant_in_request(request):
            tenant = self.resolve_tenant_for_user(request, user_entity.id)
            return UserIdentity.from_user_entity(user_entity, tenant)
        elif request:
            return UserIdentity.from_user_entity_without_tenant(user_entity)
        else:
            tenant = self.get_active_tenant_for_user(user_entity.id)
            return UserIdentity.from_user_entity(user_entity, tenant)
