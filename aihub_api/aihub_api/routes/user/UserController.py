from typing import Annotated, Optional

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Security

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.MyUserDTO import MyUserDTO
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
            return await UserService.get_logged_in_user(user)

        return self

    def get_my_dashboard_settings(self, route: str = "/dashboard") -> "UserController":
        """
        Registers an endpoint to retrieve the currently logged-in user's dashboard settings.
        Default route: GET /user/dashboard
        """

        @self.router.get(route, tags=self.tags)
        async def get_my_dashboard_settings(
            user: AuthenticatedUser = Security(self.auth),
        ) -> Optional[DashboardDTO]:
            """
            Returns a `DashboardDTO` representing the user's dashboard settings, or null if none exist.
            """
            return UserService.get_user_dashboard_settings(user)

        return self

    def update_my_dashboard_settings(self, route: str = "/dashboard") -> "UserController":
        """
        Registers an endpoint to update the currently logged-in user's dashboard settings.
        Default route: PUT /user/dashboard
        """

        @self.router.put(route, tags=self.tags, status_code=204)
        async def update_my_dashboard_settings(
            dashboard_dto: Annotated[DashboardDTO, Body],
            user: AuthenticatedUser = Security(self.auth),
        ) -> None:
            """
            Updates the user's dashboard settings.
            Accepts a `DashboardDTO` in the request body.
            """
            await UserService.update_user_dashboard_settings(user, dashboard_dto)
            return None

        return self
