from abc import ABC, abstractmethod

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity


class BearerAuthHandler(AuthHandler, ABC):
    @abstractmethod
    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        """
        Given a FastAPI Request, this method must either return a UserIdentity or raise an HTTPException.
        """
        pass
