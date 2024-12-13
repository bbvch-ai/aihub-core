import logging
from random import seed
from typing import List, Optional

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api_core.i18n.middleware.I18nMiddleware import I18nMiddleware
from api_core.runners.lifetime.lifetime_manager import lifetime_manager
from lib_core.infrastructure.azure.BaseConfig import BaseConfig


logger = logging.getLogger(__name__)

seed(0)



class ApiRunner:

    def __init__(
            self,
            title: str = "AI Hub",
            description: str = "AI Hub Backend",
            origins: Optional[List[str]] = None,
            debug: bool = False,
    ):
        self.app = FastAPI(
            title=title,
            description=description,
            version=BaseConfig().VERSION or ".dev",
            lifespan=lifetime_manager,
            debug=debug,
        )

        origins = origins or ["http://localhost:3000"]
        if BaseConfig().FRONTEND_ORIGIN:
            origins += [item.strip() for item in BaseConfig().FRONTEND_ORIGIN.split(",")]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=r"https://.*\.ai-agents\.ch",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.app.add_middleware(I18nMiddleware)

