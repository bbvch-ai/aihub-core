import logging
from random import seed
from typing import List, Optional

from fastapi.routing import APIRoute

from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.AzureBaseConfig import AzureBaseConfig
from aihub_lib.routes.Controller import Controller
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from aihub_api.i18n.middleware.I18nMiddleware import I18nMiddleware
from aihub_api.runners.lifetime.lifetime_manager import lifetime_manager

logger = logging.getLogger(__name__)

seed(0)


class ApiRunner:
    """
    A utility class for constructing and running a FastAPI-based API application,
    integrating multiple controllers, middleware, and optional frontend static files.

    ### Why Use ApiRunner?
    Instead of manually piecing together a FastAPI application, CORS middleware,
    internationalization layers, and controllers, `ApiRunner` centralizes this setup.
    It:
    - Builds a base app and a nested API app.
    - Applies CORS and i18n middleware.
    - Mounts controllers under a specified API path.
    - Optionally serves a frontend directly from the same server, simplifying deployment.

    ### Key Features
    - **Separation of Concerns:** Distinguishes between a base application (for static files or other mounts)
      and the API application (serving JSON routes under a given prefix).
    - **Integration with Config:** Pulls version info, allowed origins, and other details from `BaseConfig`.
    - **Easy Controller Mounting:** Controllers that subclass `Controller` can be attached with a simple `.mount()` call.
    - **Optional Frontend Integration:** Serve a React or Vue frontend directly by calling `.mount_frontend(directory)`.

    ### Usage
    ```python
    runner = ApiRunner(api_path="/api/v1", title="My API", debug=True)
    runner.mount(MyController())  # Mounting a controller
    runner.mount_frontend("path/to/frontend/dist")  # Serve frontend if desired
    app = runner.get_app()  # This is the main FastAPI instance to run
    ```

    You can then run `app` using `uvicorn` or another ASGI server.
    """

    def __init__(
        self,
        api_path: str = "/api/v1",
        title: str = "AI Hub",
        description: str = "AI Hub Backend",
        origins: Optional[List[str]] = None,
        debug: bool = False,
    ):
        self.title = title
        self.description = description
        self.origins = origins
        self.debug = debug

        # Create the base and API apps
        self._base_app = self._get_base_app()
        self._api_app = self._get_api_app()
        self._api_app.state = self._base_app.state

        # Mount the API under the specified path
        self._base_app.mount(api_path, self._api_app)

    def get_app(self) -> FastAPI:
        """
        Returns the main FastAPI application instance, which can be run using an ASGI server.
        """
        return self._base_app

    def _get_base_app(self) -> FastAPI:
        """
        Creates the base FastAPI application, responsible for app lifecycle management (lifespan),
        possibly serving static files, and holding shared state.
        """
        return FastAPI(
            title=self.title,
            description=self.description,
            version=ApiConfig().VERSION or ".dev",
            lifespan=lifetime_manager,
            debug=self.debug,
        )

    def _get_api_app(self) -> FastAPI:
        """
        Creates the API FastAPI application that will be mounted under `api_path`.
        Applies middleware like CORS and i18n. The controllers are mounted onto this app.
        """
        app = FastAPI(
            title=self.title,
            description=self.description,
            version=ApiConfig().VERSION or ".dev",
            debug=self.debug,
        )

        origins = self.origins or ["http://localhost:8080"]
        if ApiConfig().FRONTEND_ORIGIN:
            origins += [item.strip() for item in ApiConfig().FRONTEND_ORIGIN.split(",")]

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=r"https://.*\.ai-agents\.ch",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Internationalization middleware
        app.add_middleware(I18nMiddleware)
        return app

    def mount(self, *controllers: Controller) -> "ApiRunner":
        """
        Mounts one or more controllers (each subclass of Controller) onto the API application.
        This attaches the controller’s routes under the prefix defined in the controller itself.
        """
        for controller in controllers:
            controller.mount(self._api_app)
        for route in self._api_app.routes:
            if isinstance(route, APIRoute):
                route.operation_id = route.name  # in this case, 'read_items'
        return self

    def mount_frontend(self, directory: str) -> "ApiRunner":
        """
        Mount a static frontend (e.g., a React build directory) at the base "/" path of the app.
        This allows serving the SPA directly from the same server that handles API requests.
        """
        self._base_app.mount("/", StaticFiles(directory=directory, html=True), name="static")
        return self
