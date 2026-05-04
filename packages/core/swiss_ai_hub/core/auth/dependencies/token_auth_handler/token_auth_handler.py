import asyncio
import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from swiss_ai_hub.core.auth.dependencies.bearer_auth_handler import BearerAuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken

logger = logging.getLogger(__name__)


class TokenAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency for token-based authentication.

    Validates bearer tokens from the database and returns user identity using
    Keycloak for profile data. Derives ``is_sys_admin`` from the token owner's
    Keycloak realm roles so a token holder has the same sysadmin capability as
    they would when logging in via OAuth2.
    """

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        token_str = bearer_token.credentials
        return await self.authenticate_token(token_str, request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        """
        Authenticates a user using a bearer token string.

        Resolves tenant context from the optional request parameter, falling back to
        the user's active tenant when the request carries none.
        """
        access_token = self.verify_token(token_str)
        keycloak_user, realm_roles = await asyncio.gather(
            KeycloakAdminService.get_user_by_id(access_token.user_oid),
            KeycloakAdminService.get_user_realm_roles(access_token.user_oid),
        )
        is_sys_admin = SYS_ADMIN_ROLE in realm_roles
        return await self.build_identity(
            user_id=access_token.user_oid,
            name=keycloak_user.name,
            email=keycloak_user.email,
            request=request,
            is_sys_admin=is_sys_admin,
        )

    @staticmethod
    def verify_token(token_str: str) -> BearerToken:
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")
        try:
            return BearerToken.verify_token(token_str)
        except ValueError as e:
            logger.warning(f"Token authentication failed: {e}")
            raise HTTPException(status_code=401, detail=str(e))
