import abc
from typing import TYPE_CHECKING

from aihub_api.i18n.ApiLocaleHandler import ApiLocaleHandler
from fastapi import APIRouter, FastAPI

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler
from aihub_lib.i18n.LocaleString import LocaleString

if TYPE_CHECKING:
    from aihub_api.runners.ApiRunner import ApiRunner


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

    def __init__(self, route: str, auth: AuthHandler | None = None, is_admin_only=False):
        self.base_route: str = route
        self.auth: AuthHandler = auth or NoAuthHandler()
        self.router: APIRouter = APIRouter()

        self.is_admin_only = is_admin_only

    @property
    def tags(self):
        return [ApiLocaleHandler().extract(self.name)]

    def mount(self, app: FastAPI, runner: "ApiRunner"):
        """
        Attach this controller’s router to the given FastAPI application using the base_route prefix.
        This final step exposes all endpoints defined in this controller to incoming requests.
        """
        app.include_router(self.router, prefix=self.base_route)
