import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.access.entities.BearerToken import BearerToken

logger = logging.getLogger(__name__)


class TokenAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency that implements token-based authentication.

    This dependency expects a Bearer token in the `Authorization` header of the incoming request.
    It performs the following steps:
      1. Extracts the token from the header.
      2. Validates the token by performing a database lookup via `AccessToken.verify_token`.
      3. Checks that the token is correctly formatted, exists in the database, and is not expired.
      4. Maps the token's stored API user data onto an `UserIdentity` instance.

    If any of these checks fail (e.g., if the token is missing, malformed, not found, or expired),
    an `HTTPException` with a 401 Unauthorized status is raised.
    """

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        token_str = bearer_token.credentials
        return await self.authenticate_token(token_str)

    async def authenticate_token(self, token_str: str) -> UserIdentity:
        """
        Authenticates a user using a bearer token string directly.
        Used for WebSocket authentication.
        """
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")

        try:
            access_token = BearerToken.verify_token(token_str)
        except ValueError as e:
            logger.warning(f"Token authentication failed: {e}")
            raise HTTPException(status_code=401, detail=str(e))

        return await self._identity_provider.get_user_identity_by_oid(access_token.user_oid)
