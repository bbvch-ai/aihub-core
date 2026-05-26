# SPDX-License-Identifier: LicenseRef-Proprietary
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
from swiss_ai_hub.api.i18n.middleware.i18n_middleware import I18nMiddleware
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings, NatsSettings, RedisSettings
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner
from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook
from swiss_ai_hub.core.routes import Controller

logger = logging.getLogger(__name__)


class SysadminApiRunner:
    """Standalone runner for the sysadmin plane.

    Deliberately does NOT inherit ``swiss_ai_hub.api.ApiRunner``. The main API's
    runner builds an MCP server and wires a lifespan that connects Milvus, S3,
    Neo4j, WebSocket plumbing, discovery services and provisioners — none of
    which the sysadmin plane needs, and inheriting it forced a fragile
    "lite vs full lifespan" override.

    This runner builds a plain FastAPI app mounted under ``/api/v1`` with a
    deliberately medium-sized lifespan: **MongoDB + NATS + Redis**. That set is
    enough to mount any ``packages/api`` controller that doesn't depend on
    Milvus / S3 / WebSocket / discovery (currently: ``UserController``,
    ``RoleController``, ``MyAccountController.get_my_identity``,
    ``AuthProviderController``). NATS isn't actively used by the mounted
    controllers' code paths today — it's wired because ``use_nats`` is a
    declared dependency on a handful of endpoints (e.g. ``UserController.get_user``)
    and FastAPI resolves dependencies eagerly. ``I18nMiddleware`` is wired so
    ``use_locale`` resolves cleanly for the same reason.

    Adding more infra (Milvus, S3, Neo4j, WebSocket, discovery) here is fine
    when a future mounted controller needs it — match the source pattern in
    ``packages/api/.../lifetime_manager.py`` and extend the closure below.
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

        cors_origins = list(origins or [])
        if AIHubSettings().FRONTEND_ORIGIN:
            cors_origins += [item.strip() for item in AIHubSettings().FRONTEND_ORIGIN.split(",")]
        self._api_app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # I18nMiddleware sets ``request.state.locale`` so ``use_locale`` resolves
        # for endpoints that declare it (currently dormant on sysadmin-api, but
        # any mounted ``packages/api`` controller using ``use_locale`` works).
        self._api_app.add_middleware(I18nMiddleware)

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
        api_app = self._api_app

        @asynccontextmanager
        async def lifespan(_: Starlette) -> AsyncGenerator:
            """MongoDB + NATS + Redis lifespan for sysadmin-api.

            The closure captures ``api_app`` so resources land on the inner
            FastAPI app's ``state`` — that's the app FastAPI dependencies
            (``use_nats``, ``use_redis``) reach via ``request.app.state``.
            """
            print(AIHubSettings().startup_banner)
            logger.info("Sysadmin API starting: MongoDB + NATS + Redis")
            connect(
                db=AIHubSettings().MONGO_MAIN_DB_NAME,
                host=MongoSettings().CONNECTION_STRING.get_secret_value(),
                uuidRepresentation="standard",
            )
            redis = RedisSettings.create_client()
            nc = await NatsSettings.create_client()
            api_app.state.nc = nc
            api_app.state.redis = redis

            # MongoEngine signals are per-process — mutations through sysadmin-api
            # need their own listener to mirror access changes to OpenWebUI.
            AccessChangeHook.connect(OpenWebuiProvisioner(redis=redis))

            try:
                yield
            finally:
                logger.info("Sysadmin API shutting down")
                await nc.drain()
                await redis.close()
                disconnect()

        return Starlette(
            routes=[Mount(self.api_path, app=api_app)],
            lifespan=lifespan,
        )
