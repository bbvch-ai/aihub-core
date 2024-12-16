import logging
from random import seed
from typing import List, Optional

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from api_core.i18n.middleware.I18nMiddleware import I18nMiddleware
from api_core.routes.Controller import Controller
from api_core.runners.lifetime.lifetime_manager import lifetime_manager
from lib_core.infrastructure.azure.BaseConfig import BaseConfig


logger = logging.getLogger(__name__)

seed(0)



class ApiRunner:

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

        self._base_app = self._get_app()
        self._api_app = self._get_app()

        self._base_app.mount(api_path, self._api_app)


    def _get_app(self):
        app = FastAPI(
            title=self.title,
            description=self.description,
            version=BaseConfig().VERSION or ".dev",
            lifespan=lifetime_manager,
            debug=self.debug,
        )

        origins = self.origins or ["http://localhost:3000"]
        if BaseConfig().FRONTEND_ORIGIN:
            origins += [item.strip() for item in BaseConfig().FRONTEND_ORIGIN.split(",")]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=r"https://.*\.ai-agents\.ch",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.add_middleware(I18nMiddleware)
        return app

    def mount(self, *controllers: Controller) -> "ApiRunner":
        for controller in controllers:
            controller.mount(self._api_app)
        return self

    def mount_frontend(self, directory: str) -> "ApiRunner":
        self._base_app.mount("/", StaticFiles(directory=directory, html=True), name="static")
        return self