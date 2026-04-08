import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from swiss_ai_hub.core.auth.dependencies.bearer_auth_handler import BearerAuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

logger = logging.getLogger(__name__)


class TokenAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency for token-based authentication.

    Validates bearer tokens from the database and returns user identity
    using Keycloak for profile data.
    """

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        token_str = bearer_token.credentials
        return await self.authenticate_token(token_str, request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        """
        Authenticates a user using a bearer token string.

        Resolves tenant context from the optional request parameter or uses the default tenant.
        """
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")

        try:
            access_token = BearerToken.verify_token(token_str)
        except ValueError as e:
            logger.warning(f"Token authentication failed: {e}")
            raise HTTPException(status_code=401, detail=str(e))

        user_id = access_token.user_oid

        # Resolve tenant context from request or use default
        if request:
            tenant = await self.resolve_tenant_for_user(request, user_id)
        else:
            tenant = await self.get_active_tenant_for_user(user_id)

        roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
        keycloak_user = await KeycloakAdminService.get_user_by_id(user_id)

        return UserIdentity(
            id=user_id,
            name=keycloak_user.name,
            email=keycloak_user.email,
            roles=roles,
            acting_within_tenant=tenant,
        )
