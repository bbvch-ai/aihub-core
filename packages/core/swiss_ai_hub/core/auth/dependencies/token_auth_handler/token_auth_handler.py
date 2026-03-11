import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mongoengine import DoesNotExist

from swiss_ai_hub.core.auth.dependencies.bearer_auth_handler import BearerAuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity

logger = logging.getLogger(__name__)


class TokenAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency for token-based authentication.

    Validates bearer tokens from the database and returns user identity
    directly from UserEntity.
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

        try:
            user = UserEntity.by_oid(access_token.user_oid)
        except DoesNotExist:
            raise HTTPException(status_code=401, detail="User not found.")

        # Resolve tenant context from request or use default
        if request:
            tenant = self.resolve_tenant_for_user(request, user.id)
        else:
            # Fallback for contexts without request (e.g., WebSocket)
            tenant = self.get_default_tenant_for_user(user.id)

        return UserIdentity.from_user_entity(user, tenant)
