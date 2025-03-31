import abc
from abc import abstractmethod
from typing import AsyncContextManager, List, Optional, Set

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.staticfiles import StaticFiles

from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.routes.Controller import Controller


class Runner(abc.ABC):
    """
    An abstract base class for constructing and running FastAPI-based applications
    with consistent patterns for mounting controllers and managing application lifecycle.

    ### Why Use Runner?
    The `Runner` class provides a standardized foundation for creating API services with FastAPI.
    It handles common patterns like:
    - Creating a base application and a nested API application
    - Applying middleware and configuration
    - Mounting controllers under a specified API path
    - Managing application lifecycle through an abstract lifetime manager
    - Optionally serving static frontend files

    ### Key Features
    - **Dual Application Architecture:** Distinguishes between a base application (for static files or other mounts)
      and the API application (serving routes under a given prefix).
    - **Integration with Config:** Pulls version info and other details from `ApiConfig`.
    - **Easy Controller Mounting:** Controllers that subclass `Controller` can be attached with a simple `.mount()` call.
    - **Abstract Lifetime Management:** Each implementation must provide a `lifetime_manager` for handling async startup/shutdown.
    - **Optional Frontend Integration:** Serve a frontend directly by calling `.mount_frontend(directory)`.

    ### Usage
    ```python
    # Typically you'd use a concrete implementation like ApiRunner or BotRunner
    runner = ConcreteRunner(api_path="/api/v1", title="My API", debug=True)
    runner.mount(MyController())  # Mounting a controller
    runner.mount_frontend("path/to/frontend/dist")  # Serve frontend if desired
    app = runner.get_app()  # This is the main FastAPI instance to run
    ```

    You can then run `app` using `uvicorn` or another ASGI server.
    """

    def __init__(
        self,
        api_path: str = "/api/v1",
        title: str = "AI Hub Service",
        description: str = "AI Hub",
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

        self.controllers: Set[Controller] = set()

    @property
    @abstractmethod
    def lifetime_manager(self) -> AsyncContextManager:
        pass

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
            lifespan=self.lifetime_manager,
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

        return app

    def mount(self, *controllers: Controller) -> "Runner":
        """
        Mounts one or more controllers (each subclass of Controller) onto the API application.
        This attaches the controller’s routes under the prefix defined in the controller itself.
        """
        for controller in controllers:
            controller.mount(self._api_app, self)
            self.controllers.add(controller)

        # Ensures that openapi docs are generated with the method name as the operation name
        for route in self._api_app.routes:
            if isinstance(route, APIRoute):
                route.operation_id = route.name

        return self

    def mount_frontend(self, directory: str) -> "Runner":
        """
        Mount a static frontend (e.g., a React build directory) at the base "/" path of the app.
        This allows serving the SPA directly from the same server that handles API requests.
        """
        self._base_app.mount("/", StaticFiles(directory=directory, html=True), name="static")
        return self
