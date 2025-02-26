from aihub_api.routes.user.dto.MyUserDTO import MyUserDTO
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Security

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
        .get_my_user()
        .mount(app)
    ```

    Once mounted, calling `GET /user/me` returns user data like name, email, etc., depending on `UserDTO`.
    """
    name = LocaleString(en="User")
    description = LocaleString(en="Manage own user")
    icon = "solar:password-bold"

    def __init__(self, route: str = "/user", auth: AuthHandler | None = None, is_admin_only=False):
        super().__init__(route, auth, is_admin_only=is_admin_only)

    def get_my_user(self, route: str = "/me") -> "UserController":
        @self.router.get(route, tags=self.tags)
        async def get_my_user(
            user: AuthenticatedUser = Security(self.auth),
        ) -> MyUserDTO:
            """
            Returns a `UserDTO` representing the currently logged-in user.
            """
            return UserService.get_logged_in_user(user)

        return self
