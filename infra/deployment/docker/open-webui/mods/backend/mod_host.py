import asyncio
import json
import mimetypes
import os
from collections import OrderedDict
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path as FilePath
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path, Request, Response
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from aihub_mods.frontend_archive import FrontendArchive
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.hub_client import HubClient
from aihub_mods.mod_runtime import ModRuntime
from aihub_mods.global_mod_control import GlobalModControl
from aihub_mods.global_mod_runtime import GlobalModRuntime
from aihub_mods.global_mod_store import GlobalModStore

Tenant = Annotated[str, Path(min_length=1, max_length=255)]
View = Annotated[str, Path(pattern=r"^[a-f0-9]{32}$")]
Revision = Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")]
ModId = Annotated[str, Path(max_length=64, pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")]


class ModHost:
    CACHE_BYTES = 32 * 1024 * 1024

    def __init__(self, client: HubClient, compatibility: bytes, global_directory: FilePath | None = None) -> None:
        self.client = client
        self.compatibility = compatibility
        self.archives: OrderedDict[str, FrontendArchive] = OrderedDict()
        self.archive_lock = asyncio.Lock()
        self.runtime = ModRuntime(self)
        self.global_runtime = GlobalModRuntime(GlobalModStore(global_directory, compatibility), self.runtime) if global_directory else None

    def install(self, app: FastAPI, verified_user: Callable[..., Any]) -> None:
        router = APIRouter(prefix="/_aihub/mods", dependencies=[Depends(self._same_origin)])
        if self.global_runtime is not None:
            GlobalModControl(self.global_runtime.store, os.environ.get("SCIM_TOKEN", "")).install(router)
        self._configuration_routes(router, verified_user)
        self._file_routes(router, verified_user)
        self._api_routes(router, verified_user)
        previous_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def lifespan(application: FastAPI) -> AsyncIterator[Any]:
            try:
                if self.global_runtime is not None:
                    await self.global_runtime.start(application)
                async with previous_lifespan(application) as state:
                    if self.global_runtime is not None:
                        await self.global_runtime.mark_ready()
                    yield state
            finally:
                if self.global_runtime is not None:
                    await self.global_runtime.close()
                await self.runtime.close()
                await self.client.http.aclose()

        app.router.lifespan_context = lifespan
        app.state.aihub_mods = self
        start = len(app.router.routes)
        app.include_router(router)
        # Upstream's frontend catch-all otherwise consumes the new routes.
        added = app.router.routes[start:]
        del app.router.routes[start:]
        app.router.routes[0:0] = added
        app.openapi_schema = None

    @staticmethod
    def _same_origin(request: Request) -> None:
        origin = request.headers.get("origin")
        expected = f"{request.url.scheme}://{request.url.netloc}"
        if (origin and origin != expected) or request.headers.get("sec-fetch-site") in {"same-site", "cross-site"}:
            raise HTTPException(403, "Mod delivery requires a same-origin request.")

    @staticmethod
    def _response(content: bytes, media_type: str) -> Response:
        return Response(content, media_type=media_type, headers={
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
            "Cross-Origin-Resource-Policy": "same-origin",
        })

    def _configuration_routes(self, router: APIRouter, verified_user: Callable[..., Any]) -> None:
        @router.get("/callables.json")
        async def get_callables() -> Response:
            return self._response(json.dumps(CallableRegistry.catalog, sort_keys=True).encode(), "application/json")

        @router.post("/tenants/{tenant_id}/configuration")
        async def get_configuration(
            tenant_id: Tenant, request: Request, user: Annotated[Any, Depends(verified_user)],
        ) -> Response:
            if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise HTTPException(415, "Send a JSON request.")
            content = await self.client.request(
                "POST", tenant_id, "/configuration", name=user.name, email=user.email, content=self.compatibility,
            )
            return self._response(content, "application/json")

    def _file_routes(self, router: APIRouter, verified_user: Callable[..., Any]) -> None:
        prefix = "/tenants/{tenant_id}/views/{view_id}/publications/{revision}"

        @router.get(prefix + "/publication.json")
        async def get_manifest(
            tenant_id: Tenant, view_id: View, revision: Revision, user: Annotated[Any, Depends(verified_user)],
        ) -> Response:
            archive = await self._archive(tenant_id, revision, user)
            return self._response(archive.read("publication.json", manifest=True), "application/json")

        @router.get(prefix + "/files/{filename:path}")
        async def get_file(
            tenant_id: Tenant, view_id: View, revision: Revision, filename: str,
            user: Annotated[Any, Depends(verified_user)],
        ) -> Response:
            archive = await self._archive(tenant_id, revision, user)
            media_type = "text/javascript" if filename.endswith(".mjs") else mimetypes.guess_type(filename)[0]
            return self._response(archive.read(filename), media_type or "application/octet-stream")

    def _api_routes(self, router: APIRouter, verified_user: Callable[..., Any]) -> None:
        prefix = "/tenants/{tenant_id}/mods/{mod_id}/api"

        @router.api_route(prefix + "/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"])
        async def handle(
            tenant_id: Tenant, mod_id: ModId, path: str, request: Request,
            user: Annotated[Any, Depends(verified_user)],
        ) -> Response:
            identity = {key: getattr(user, key) for key in ("id", "name", "email", "role")}
            result = await self.runtime.handle(tenant_id, mod_id, path, request, identity)
            if isinstance(result, Response):
                return result
            return JSONResponse(jsonable_encoder(result), headers={"Cache-Control": "no-store"})

        @router.api_route("/tenants/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"])
        async def unknown_mod_route() -> Response:
            raise HTTPException(404, "Mod route not found.")

    async def _archive(self, tenant_id: str, revision: str, user: Any) -> FrontendArchive:
        suffix = f"/publications/{revision}/frontend"
        await self.client.request("HEAD", tenant_id, suffix, name=user.name, email=user.email, compatibility=self.compatibility)
        async with self.archive_lock:
            if revision not in self.archives:
                content = await self.client.request("GET", tenant_id, suffix, name=user.name, email=user.email, compatibility=self.compatibility)
                archive = FrontendArchive(revision, content)
                if json.loads(archive.read("publication.json", manifest=True))["compatibility"] != json.loads(self.compatibility):
                    raise HTTPException(409, "Mod publication belongs to another host version. Reload the chat.")
                self.archives[revision] = archive
            self.archives.move_to_end(revision)
            while sum(len(archive.content) for archive in self.archives.values()) > self.CACHE_BYTES:
                self.archives.popitem(last=False)
            return self.archives[revision]
