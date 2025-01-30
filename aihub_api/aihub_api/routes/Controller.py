import abc
from typing import Callable, Any

from fastapi import APIRouter, FastAPI

from aihub_api.auth.dependencies.no_auth.use_no_auth_user import use_no_auth_user


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

    def __init__(self, route: str, auth: Callable[..., Any] = None):
        self.base_route = route
        self.auth = auth or use_no_auth_user
        self.router = APIRouter()

    def mount(self, app: FastAPI):
        """
        Attach this controller’s router to the given FastAPI application using the base_route prefix.
        This final step exposes all endpoints defined in this controller to incoming requests.
        """
        app.include_router(self.router, prefix=self.base_route)
