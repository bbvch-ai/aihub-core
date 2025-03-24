import abc
from abc import abstractmethod
from typing import AsyncContextManager, List, Optional, Set

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.staticfiles import StaticFiles

from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.routes.Controller import Controller


class Runner(abc.ABC):
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
