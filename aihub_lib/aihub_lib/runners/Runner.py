import abc
from abc import abstractmethod
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Self

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.applications import Starlette
from starlette.routing import Mount

from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
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
    - **Integration with Config:** Pulls version info and other details from `AIHubSettings`.
    - **Easy Controller Mounting:** Controllers that subclass `Controller` can be attached with a simple
      `.mount()` call.
    - **Abstract Lifetime Management:** Each implementation must provide a `lifetime_manager`
      for handling async startup/shutdown.
    - **Optional Frontend Integration:** Serve a frontend directly by calling `.mount_frontend(directory)`.

    ### Usage
    ```python
    # Typically you'd use a concrete implementation like ApiRunner or BotRunner
    runner = ConcreteRunner(api_path="/api/v1", title="My API")
    runner.mount(MyController())  # Mounting a controller
    runner.mount_frontend("path/to/frontend/dist")  # Serve frontend if desired
    app = runner.create_app()  # This is the main FastAPI instance to run
    ```

    You can then run `app` using `uvicorn` or another ASGI server.
    """

    def __init__(
        self,
        api_path: str = "/api/v1",
        title: str = "AI Hub Service",
        description: str = "AI Hub",
        origins: list[str] | None = None,
    ):
        self.title = title
        self.description = description
        self.origins = origins

        self._api_app = self._get_api_app()

        # Mount the API under the specified path
        self.api_path = api_path

        self.controllers: set[Controller] = set()

    @property
    @abstractmethod
    def lifetime_manager(self) -> Callable[[FastAPI], AbstractAsyncContextManager]:
        pass

    def create_app(self) -> Starlette:
        """
        Returns the main FastAPI application instance, which can be run using an ASGI server.
        """
        return Starlette(
            routes=[
                Mount(self.api_path, app=self._api_app),
            ],
            lifespan=self.lifetime_manager,
        )

    def _get_api_app(self) -> FastAPI:
        """
        Creates the API FastAPI application that will be mounted under `api_path`.
        Applies middleware like CORS and i18n. The controllers are mounted onto this app.
        """
        app = FastAPI(
            title=self.title,
            description=self.description,
            version=AIHubSettings().API_VERSION,
            debug=AIHubSettings().API_DEBUG_MODE,
            redirect_slashes=True,
        )

        return app

    def mount(self, *controllers: Controller) -> Self:
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
