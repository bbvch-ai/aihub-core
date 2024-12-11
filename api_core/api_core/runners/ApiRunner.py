import logging
from typing import List

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api_core.middleware.I18nMiddleware import I18nMiddleware
from api_core.runners.lifetime.lifetime_manager import lifetime_manager
from lib_core.infrastructure.azure.BaseConfig import BaseConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('pymongo').setLevel(logging.INFO)

logger = logging.getLogger(__name__)





class ApiRunner:

    def __init__(
            self,
            title: str,
            description: str,
            origins=List[str]
    ):
        self.app = FastAPI(
            title=title,
            description=description,
            version=BaseConfig().VERSION or ".dev",
            lifespan=lifetime_manager
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=r"https://.*\.ai-agents\.ch",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.app.add_middleware(I18nMiddleware)

    def run(self) -> None:
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=8000)