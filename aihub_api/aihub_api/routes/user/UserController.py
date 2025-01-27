from typing import Callable, Any

from fastapi import Depends, FastAPI

from aihub_api.auth.AuthenticatedUser import AuthenticatedUser
from aihub_api.routes.Controller import Controller
from aihub_api.routes.user.dto.UserDTO import UserDTO
from aihub_api.routes.user.UserService import UserService


class UserController(Controller):
    """
    A controller that manages user-related endpoints, particularly retrieving the currently logged-in user.

    ### Why UserController?
    In many applications, authenticated users may want to retrieve their own profile or check who they are
    logged in as. The `UserController` provides a simple endpoint that returns a `UserDTO` for the authenticated user.

    ### Endpoint
    - `GET /user/me`: Returns information about the currently authenticated user.

    ### Authentication
    This endpoint relies on the configured `auth` dependency to ensure that the user is authenticated.
    If no auth dependency is provided, no authentication is applied.

    ### Usage
    ```python
    app = FastAPI()
    UserController(auth=some_auth_dependency)
        .get_user()
        .mount(app)
    ```

    Once mounted, calling `GET /user/me` returns user data like name, email, etc., depending on `UserDTO`.
    """

    def __init__(self, route: str = "/user", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_user(self, route: str = "/me") -> "UserController":
        @self.router.get(route)
        async def get_user(
            user: AuthenticatedUser = Depends(self.auth),
        ) -> UserDTO:
            """
            Returns a `UserDTO` representing the currently logged-in user.
            """
            return UserService.get_logged_in_user(user)

        return self
