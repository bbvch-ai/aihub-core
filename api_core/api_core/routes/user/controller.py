from typing import Callable, Any

from fastapi import APIRouter, Depends

from api_core.auth.AuthenticatedUser import AuthenticatedUser


def user_controller_factory(user_auth_strategy: Callable[..., Any]):

    user_router = APIRouter()

    @user_router.get("/me")
    async def get_user(
            user: AuthenticatedUser = Depends(user_auth_strategy),
    ) -> AuthenticatedUser:
        return user

    return user_router
