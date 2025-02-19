from abc import ABC, abstractmethod

from fastapi import Request

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser


class AuthHandler(ABC):
    @abstractmethod
    async def __call__(self, request: Request) -> AuthenticatedUser:
        """
        Given a FastAPI Request, this method must either return an AuthenticatedUser or raise an HTTPException.
        """
        pass
