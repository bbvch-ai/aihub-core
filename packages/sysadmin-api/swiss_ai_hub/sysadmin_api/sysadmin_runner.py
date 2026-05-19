import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Self

from fastapi import FastAPI
from fastapi.routing import APIRoute
from mongoengine import connect, disconnect
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.routes import Controller

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _sysadmin_lifespan(_: Starlette) -> AsyncGenerator:
    """The entire lifespan of the sysadmin plane: connect to MongoDB, nothing else.

    sysadmin-api does not publish or subscribe to NATS, does not stream over
    WebSockets, and does not touch Milvus / Redis / S3 / Neo4j. Keycloak access
    is REST and initialised lazily per call. This is deliberately the whole
    story — there is no "full" variant to fall back to.
    """
    print(AIHubSettings().startup_banner)
    logger.info("Sysadmin API starting: connecting to MongoDB")
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    try:
        yield
    finally:
        logger.info("Sysadmin API shutting down: disconnecting from MongoDB")
        disconnect()


class SysadminApiRunner:
    """Standalone runner for the sysadmin plane.

    Deliberately does NOT inherit ``swiss_ai_hub.api.ApiRunner``. The main API's
    runner builds an MCP server and wires a lifespan that connects NATS, Milvus,
    Redis, S3, WebSocket plumbing, discovery services and provisioners — none of
    which the sysadmin plane needs, and inheriting it forced a fragile "lite vs
    full lifespan" override. This runner builds a plain FastAPI app mounted under
    ``/api/v1`` with a MongoDB-only lifespan and CORS. No MCP, no i18n middleware
    (sysadmin endpoints do not consume request locale), no OpenAPI tenant_id
    injection (sysadmin-api has no tenant-prefixed routes).
    """

    def __init__(
        self,
        *,
        title: str = "Swiss AI Hub Sysadmin API",
        description: str = "System administration plane.",
        api_path: str = "/api/v1",
        origins: list[str] | None = None,
    ):
        self.api_path = api_path
        self.controllers: set[Controller] = set()
        self._api_app = FastAPI(
            title=title,
            description=description,
            version=AIHubSettings().VERSION,
            debug=AIHubSettings().API_DEBUG_MODE,
            redirect_slashes=True,
        )

        cors_origins = origins or ["http://localhost:8080"]
        if AIHubSettings().FRONTEND_ORIGIN:
            cors_origins += [item.strip() for item in AIHubSettings().FRONTEND_ORIGIN.split(",")]
        self._api_app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def mount(self, *controllers: Controller) -> Self:
        for controller in controllers:
            controller.mount(self._api_app, self)
            self.controllers.add(controller)
        # Match ApiRunner: operation_id == route name so the generated SDK uses
        # readable method names.
        for route in self._api_app.routes:
            if isinstance(route, APIRoute):
                route.operation_id = route.name
        return self

    def create_app(self) -> Starlette:
        return Starlette(
            routes=[Mount(self.api_path, app=self._api_app)],
            lifespan=_sysadmin_lifespan,
        )
