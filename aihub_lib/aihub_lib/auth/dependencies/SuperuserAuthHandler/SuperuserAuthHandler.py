import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class SuperuserAuthHandler:
    """
    A FastAPI dependency for superuser authentication.

    Validates that the token matches the configured superuser token
    and returns the superuser identity from configuration.
    """

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        token_str = bearer_token.credentials
        return await self.authenticate_token(token_str)

    async def authenticate_token(self, token_str: str) -> UserIdentity:
        """Authenticates the superuser using the configured token."""
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")

        settings = SuperuserSettings()
        if token_str != settings.TOKEN.get_secret_value():
            raise HTTPException(status_code=401, detail="Invalid token.")

        return settings.get_user_identity()
