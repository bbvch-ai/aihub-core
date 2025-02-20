from abc import abstractmethod, ABC

from fastapi import Security, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler


class BearerAuthHandler(AuthHandler, ABC):
    @abstractmethod
    async def __call__(self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> AuthenticatedUser:
        """
        Given a FastAPI Request, this method must either return an AuthenticatedUser or raise an HTTPException.
        """
        pass
