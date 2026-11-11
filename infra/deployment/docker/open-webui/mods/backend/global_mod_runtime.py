import asyncio
import logging
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request

from aihub_mods.backend_package import BackendPackage
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.global_mod_context import GlobalModContext
from aihub_mods.global_mod_store import GlobalModStore
from aihub_mods.mod_runtime import ModRuntime
from aihub_mods.mod_selection import ModSelection


class GlobalModRuntime:
    def __init__(self, store: GlobalModStore, runtime: ModRuntime) -> None:
        self.store = store
        self.runtime = runtime
        self.version = -1
        self.attempted_version = -1
        self.error: str | None = None
        self.ready = False
        self.selected: list[tuple[BackendPackage, ModSelection]] = []
        self.lock = asyncio.Lock()
        self.app: FastAPI | None = None
        self.poller: asyncio.Task[None] | None = None

    async def start(self, app: FastAPI) -> None:
        self.app = app
        await asyncio.to_thread(self.store.initialize)
        await self.refresh()
        self.poller = asyncio.create_task(self._poll())

    async def _poll(self) -> None:
        while True:
            await asyncio.sleep(2)
            try:
                await self.refresh()
            except OSError:
                logging.getLogger(__name__).exception("Could not refresh global mod state; retrying on the next poll")

    async def refresh(self) -> None:
        async with self.lock:
            configuration = await asyncio.to_thread(self.store.live)
            try:
                if configuration.version != self.attempted_version:
                    self.attempted_version = configuration.version
                    selected = []
                    for mod in configuration.mods:
                        if not mod.enabled:
                            continue
                        revision, content, _ = await asyncio.to_thread(self.store.source, mod)

                        async def read_source(content: bytes = content) -> bytes:
                            return content

                        package = await self.runtime.load_package(revision, mod.mod_id, read_source)
                        selected.append((package, mod))
                    self.selected, self.version, self.error = selected, configuration.version, None
                    CallableRegistry.global_handlers = self.handlers()
            except Exception:
                # Keep the control API reachable so an invalid global selection can be repaired.
                self.error = f"Global mod version {configuration.version} failed to load; see Open WebUI logs and correct the selection."
                logging.getLogger(__name__).exception(self.error)
            await asyncio.to_thread(self.store.worker_status, self.version, self.error, self.ready)

    async def mark_ready(self) -> None:
        self.ready = True
        await asyncio.to_thread(self.store.worker_status, self.version, self.error, self.ready)

    def handlers(self, request: Request | None = None) -> dict[str, tuple[Callable[..., Any], ...]]:
        handlers: dict[str, tuple[Callable[..., Any], ...]] = {}
        for package, selection in self.selected:
            context = GlobalModContext(
                id=f"global:{self.version}", mod_id=selection.mod_id, publication=selection.publication,
                settings=selection.model_copy(deep=True).settings, app=self.app, request=request,
            )
            for target, callbacks in package.bind_overrides(context).items():
                handlers[target] = handlers.get(target, ()) + callbacks
        return handlers

    async def close(self) -> None:
        if self.poller is not None:
            self.poller.cancel()
            await asyncio.gather(self.poller, return_exceptions=True)
        self.ready = False
        await asyncio.to_thread(self.store.worker_status, self.version, self.error, False)
        CallableRegistry.global_handlers = {}
