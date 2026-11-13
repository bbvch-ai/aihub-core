import asyncio
import hmac
import os
import signal
from pathlib import Path
from typing import Annotated, Any, Literal
from zipfile import BadZipFile

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path as RoutePath, Request, Response

from aihub_mods.global_mod_configuration import GlobalModConfiguration
from aihub_mods.global_mod_store import GlobalModStore
from aihub_mods.mod_compiler import ModCompiler


class GlobalModControl:
    def __init__(self, store: GlobalModStore, token: str) -> None:
        self.store = store
        self.token = token

    def install(self, router: APIRouter) -> None:
        control = APIRouter(prefix="/control", dependencies=[Depends(self.authorize)])

        @control.post("/compile")
        async def compile_mod(request: Request) -> Response:
            content = await self.read_body(request, ModCompiler.MAX_ARCHIVE_BYTES)
            archive = await ModCompiler(self.store.directory).compile(content)
            return Response(archive, media_type="application/zip", headers={"Cache-Control": "no-store"})

        @control.get("/global")
        async def status() -> dict[str, Any]:
            return await asyncio.to_thread(self.store.status)

        @control.put("/archives/{kind}/{revision}", status_code=204)
        async def stage(
            kind: Literal["sources", "publications"], revision: Annotated[str, RoutePath(pattern=r"^[a-f0-9]{64}$")],
            request: Request,
        ) -> Response:
            content = await self.read_body(request, 16 * 1024 * 1024)
            try:
                await asyncio.to_thread(self.store.stage, kind, revision, content)
            except (ValueError, KeyError, BadZipFile) as error:
                raise HTTPException(422, str(error)) from error
            return Response(status_code=204)

        @control.put("/global")
        async def replace(request: Request) -> dict[str, Any]:
            content = await self.read_body(request, 64 * 1024)
            try:
                configuration = GlobalModConfiguration.model_validate_json(content)
                return await asyncio.to_thread(self.store.replace, configuration)
            except FileNotFoundError as error:
                raise HTTPException(409, "Stage the selected source and publication archives before saving") from error
            except (ValueError, KeyError) as error:
                raise HTTPException(422, str(error)) from error

        @control.post("/restart", status_code=202)
        async def restart(version: int, background_tasks: BackgroundTasks) -> dict[str, Any]:
            self.check_restart_environment()
            await asyncio.to_thread(self.store.request_restart, version)
            background_tasks.add_task(self.restart)
            return {"status": "restarting", "version": version}

        router.include_router(control)

    def authorize(self, request: Request) -> None:
        if not self.token:
            raise HTTPException(503, "Open WebUI mod management has no configured provisioning credential")
        supplied = request.headers.get("authorization", "")
        if not hmac.compare_digest(supplied.encode(), f"Bearer {self.token}".encode()):
            raise HTTPException(403, "Open WebUI mod management requires the platform provisioning credential")

    @staticmethod
    async def read_body(request: Request, maximum: int) -> bytes:
        result = bytearray()
        async for chunk in request.stream():
            if len(result) + len(chunk) > maximum:
                raise HTTPException(413, "Mod management request exceeds its size limit")
            result.extend(chunk)
        return bytes(result)

    @staticmethod
    def check_restart_environment() -> None:
        command = Path("/proc/1/cmdline")
        if not Path("/.dockerenv").exists() or not command.exists() or b"aihub_mods.main:app" not in command.read_bytes():
            raise HTTPException(409, "Automatic restart requires the standard Open WebUI Docker entrypoint")

    @staticmethod
    async def restart() -> None:
        await asyncio.sleep(0.1)
        os.kill(1, signal.SIGTERM)
