from abc import ABC, abstractmethod

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity


class BearerAuthHandler(AuthHandler, ABC):
    @abstractmethod
    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        """
        Given a FastAPI Request, this method must either return a UserIdentity or raise an HTTPException.
        """
        pass
