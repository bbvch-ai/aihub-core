from abc import ABC, abstractmethod

from fastapi import Request

from aihub_lib.auth.identity.UserIdentity import UserIdentity


class AuthHandler(ABC):
    """
    Base class for authentication handlers.

    Authentication handlers validate credentials and return user identities.
    """

    @abstractmethod
    async def __call__(self, request: Request) -> UserIdentity:
        """
        Given a FastAPI Request, this method must either return an UserIdentity or raise an HTTPException.
        """
        pass

    @abstractmethod
    async def authenticate_token(self, token: str) -> UserIdentity:
        """
        Authenticates a user based on a token string.
        Used for WebSocket connections and other contexts without a full Request object.
        """
        pass
