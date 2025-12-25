import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mongoengine import DoesNotExist

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.access.entities.BearerToken import BearerToken
from aihub_lib.persistence.user.UserEntity import UserEntity

logger = logging.getLogger(__name__)


class TokenAuthHandler:
    """
    A FastAPI dependency for token-based authentication.

    Validates bearer tokens from the database and returns user identity
    directly from UserEntity.
    """

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        token_str = bearer_token.credentials
        return await self.authenticate_token(token_str)

    async def authenticate_token(self, token_str: str) -> UserIdentity:
        """Authenticates a user using a bearer token string."""
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

        return UserIdentity.from_user_entity(user)
