import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class SuperuserAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency that checks whether the accessor is the global ai-hub superuser.
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

        if token_str != SuperuserSettings().TOKEN:
            raise HTTPException(status_code=401, detail="Invalid token.")

        return await self._identity_provider.get_user_identity_by_oid(SuperuserSettings().OID)
