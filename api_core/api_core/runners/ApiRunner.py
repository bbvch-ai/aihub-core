import logging
from typing import List

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api_core.runners.lifetime.lifetime_manager import lifetime_manager

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('pymongo').setLevel(logging.INFO)

logger = logging.getLogger(__name__)





class ApiRunner:

    def __init__(self, origins=List[str]):
        self.app = FastAPI(lifespan=lifetime_manager)

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=r"https://.*\.ai-agents\.ch",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def run(self):
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=8000)