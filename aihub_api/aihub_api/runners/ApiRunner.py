import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.routes.Controller import Controller
from aihub_lib.runners.Runner import Runner
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from aihub_api.i18n.ApiLocaleHandler import ApiLocaleHandler
from aihub_api.i18n.middleware.I18nMiddleware import I18nMiddleware
from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.runners.lifetime.lifetime_manager import lifetime_manager

logger = logging.getLogger(__name__)


class ApiRunner(Runner):
    """
    A concrete implementation of Runner for standard API services with
    internationalization and CORS support.

    ### Why Use ApiRunner?
    `ApiRunner` extends the base `Runner` class with specific features for standard HTTP APIs:
    - Configures CORS middleware with sensible defaults
    - Integrates internationalization (i18n) for API responses
    - Applies tag-based OpenAPI documentation organization
    - Provides a lifecycle manager tailored for API services

    ### Key Features
    - **CORS Configuration:** Automatically configures Cross-Origin Resource Sharing with
      appropriate origins from configuration.
    - **Internationalization:** Integrates with `I18nMiddleware` for multilingual support.
    - **Enhanced Documentation:** Generates OpenAPI tags and descriptions from controllers.
    - **Lifecycle Management:** Uses the API-specific lifetime manager.

    ### Usage
    ```python
    runner = ApiRunner(api_path="/api/v1", title="My API", debug=True)
    runner.mount(UserController(), ProductController())  # Mount controllers
    runner.mount_frontend("path/to/frontend/dist")  # Optional: serve frontend
    app = runner.get_app()  # Get the FastAPI instance
    ```

    Run the resulting `app` using `uvicorn` or another ASGI server.
    """

    def __init__(
        self,
        api_path: str = "/api/v1",
        title: str = "AI Hub",
        description: str = "AI Hub Backend",
        origins: list[str] | None = None,
        debug: bool = False,
    ):
        super().__init__(api_path, title, description, origins, debug)

    @property
    def lifetime_manager(self) -> Callable[[FastAPI], AbstractAsyncContextManager]:
        return lifetime_manager

    def _get_api_app(self) -> FastAPI:
        """
        Creates the API FastAPI application that will be mounted under `api_path`.
        Applies middleware like CORS and i18n. The controllers are mounted onto this app.
        """
        app = super()._get_api_app()

        origins = self.origins or ["http://localhost:8080"]
        if AIHubSettings().FRONTEND_ORIGIN:
            origins += [item.strip() for item in AIHubSettings().FRONTEND_ORIGIN.split(",")]

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
        super().mount(*controllers)

        for controller in controllers:
            if isinstance(controller, AgentController):
                self._api_app.state.agent_controller = controller

            if isinstance(controller, ProcessController):
                self._api_app.state.process_controller = controller

        self._api_app.openapi_tags = [
            {
                "name": ApiLocaleHandler().extract(controller.name),
                "description": ApiLocaleHandler().extract(controller.description),
            }
            for controller in controllers
        ]

        return self
