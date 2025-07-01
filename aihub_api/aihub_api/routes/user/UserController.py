from typing import Annotated, Optional

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
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

    def __init__(self, *, auth: AuthHandler, route: str = "/users"):
        super().__init__(auth=auth, route=route)

    def get_my_user(self, route: str = "/me") -> "UserController":
        @self.router.get(route, tags=self.tags)
        async def get_my_user(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> MyUserDTO:
            """
            Returns a `UserDTO` representing the currently logged-in user.
            """
            return await UserService.get_logged_in_user(user, identity_provider=self.auth.identity_provider)

        return self

    def get_my_dashboard(self, route: str = "/dashboard") -> "UserController":
        """
        Registers an endpoint to retrieve the currently logged-in user's dashboard settings.
        """

        @self.router.get(route, tags=self.tags)
        async def get_my_dashboard(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> Optional[DashboardDTO]:
            """
            Returns a `DashboardDTO` representing the user's dashboard settings, or null if none exist.
            """
            return UserService.get_user_dashboard(user)

        return self

    def update_my_dashboard(self, route: str = "/dashboard") -> "UserController":
        """
        Registers an endpoint to update the currently logged-in user's dashboard settings.
        """

        @self.router.put(route, tags=self.tags, status_code=204)
        async def update_my_dashboard(
            dashboard_dto: Annotated[DashboardDTO, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> None:
            """
            Updates the user's dashboard settings.
            Accepts a `DashboardDTO` in the request body.
            """
            await UserService.update_user_dashboard(user, dashboard_dto, identity_provider=self.auth.identity_provider)
            return None

        return self
