from typing import Callable, Any

from fastapi import Depends, FastAPI

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.routes.Controller import Controller
from api_core.routes.user.dto.UserDTO import UserDTO
from api_core.routes.user.UserService import UserService


class UserController(Controller):

    def __init__(self, route: str = "/user", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_user(self, route: str = "/me") -> "UserController":
        @self.router.get(route)
        async def get_user(
                user: AuthenticatedUser = Depends(self.auth),
        ) -> UserDTO:
            return UserService.get_logged_in_user(user)
        return self
