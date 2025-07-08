import abc
import logging
from typing import TYPE_CHECKING, Annotated, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString

if TYPE_CHECKING:
    from aihub_lib.runners.Runner import Runner

logger = logging.getLogger(__name__)


class Controller(abc.ABC):
    """
    A base class for controllers that define API endpoints in a structured and consistent way.

    ### Why This Class?
    In a typical FastAPI application, you might have multiple routers spread across different modules.
    By subclassing `Controller`, you establish a convention:
    - Each controller corresponds to a base route.
    - Each controller can define its own authentication dependencies.

    This makes it easier to:
    - Keep routes organized in separate classes.
    - Apply common authentication or middleware logic at the controller level.
    - Mount all controllers onto the main application in a uniform manner.

    ### Key Features
    - `base_route`: The base path under which this controller’s endpoints will be accessible.
    - `auth`: A dependency (or set of dependencies) for authentication/authorization. Defaults to `use_no_auth_user`,
      meaning no authentication is applied unless overridden.

    ### Example
    ```python
    class MyController(Controller):
        def __init__(self):
            super().__init__(route="/my-endpoints", auth=some_auth_dependency)
            # define endpoints using self.router.get(), etc.

    app = FastAPI()
    controller = MyController()
    controller.mount(app)
    ```

    This sets up all routes defined in `MyController` under `/my-endpoints`.
    """

    name = LocaleString(en="Unnamed Controller")
    description = LocaleString(en="This controller has no description.")
    icon = "lsicon:service-filled"  # https://icon-sets.iconify.design/

    def __init__(self, *, auth: AuthHandler, route: str, additionally_required_permission: Optional[str] = None):
        self.base_route: str = route
        self.auth: AuthHandler = auth or DangerousDevelopmentOnlyAuthHandler(
            identity_provider=DangerousDevelopmentOnlyIdentityProvider()
        )
        self.router: APIRouter = APIRouter()
        self.additionally_required_permission = additionally_required_permission
        self._runner: Optional["Runner"] = None

    @property
    def service_name(self):
        return self.__class__.__name__.lower().replace("controller", "")

    def user_with_permission(self, permission_template: str):
        def check_access(
            request: Request,
            user: Annotated[UserIdentity, Depends(self.auth)],
        ) -> UserIdentity:
            required_permission = permission_template.format(**request.path_params)

            access_checker = AccessChecker.from_user(user)

            if not access_checker.has_access_to_service(self.service_name):
                logger.warning(
                    f"User {user.email} does not have access to service {self.service_name}. Got roles {user.roles} with access rules {access_checker.access_rules}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: You do not have the permission to access the {self.service_name}-service.",
                )

            if self.additionally_required_permission and not access_checker.has_access(
                self.additionally_required_permission
            ):
                logger.warning(
                    f"User {user.email} does not have special permission {self.additionally_required_permission}. Got roles {user.roles} with access rules {access_checker.access_rules}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: You do not have the required additional '{self.additionally_required_permission}' permission to access this service.",
                )

            if not access_checker.has_access(required_permission):
                logger.warning(
                    f"User {user.email} does not have permission {required_permission}. Got roles {user.roles} with access rules {access_checker.access_rules}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: You do not have the required '{required_permission}' permission.",
                )
            return user

        return check_access

    @property
    def tags(self):
        return [LocaleHandler().extract(self.name)]

    def mount(self, app: FastAPI, runner: "Runner"):
        """
        Attach this controller’s router to the given FastAPI application using the base_route prefix.
        This final step exposes all endpoints defined in this controller to incoming requests.
        """
        app.include_router(self.router, prefix=self.base_route)
        self._runner = runner
