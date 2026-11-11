import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Literal
from uuid import uuid4

from fastapi import HTTPException, Request

from aihub_mods.backend_package import BackendPackage
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.mod_run import ModRun
from aihub_mods.mod_run_context import ModRunContext
from aihub_mods.mod_request_context import ModRequestContext
from aihub_mods.mod_snapshot import ModSnapshot

if TYPE_CHECKING:
    from aihub_mods.mod_host import ModHost


class ModRuntime:
    def __init__(self, host: "ModHost") -> None:
        self.host = host
        self.packages: dict[str, BackendPackage] = {}
        self.package_lock = asyncio.Lock()

    async def request_overrides(self, request: Request, user: dict[str, Any]) -> dict[str, tuple[Callable[..., Any], ...]]:
        if not hasattr(request.state, "aihub_callable_overrides"):
            request.state.aihub_callable_overrides = asyncio.create_task(self._request_overrides(request, user))
        return await asyncio.shield(request.state.aihub_callable_overrides)

    async def _request_overrides(self, request: Request, user: dict[str, Any]) -> dict[str, tuple[Callable[..., Any], ...]]:
        snapshot = await self._snapshot(request, user)
        handlers: dict[str, tuple[Callable[..., Any], ...]] = {}
        request.state.aihub_mod_bindings = {}
        for selection in snapshot.mods:
            if not selection.enabled:
                continue
            package = await self._package(snapshot, selection.publication, selection.mod_id, user)
            context = ModRequestContext(
                id=request.state.aihub_mod_view, tenant_id=snapshot.tenant_id, mod_id=selection.mod_id, publication=selection.publication,
                settings=selection.model_copy(deep=True).settings, request=request, user=dict(user),
                path=getattr(request.state, "aihub_mod_path", request.url.path),
            )
            request.state.aihub_mod_bindings[selection.mod_id] = (package, context)
            for target, callbacks in package.bind_overrides(context).items():
                handlers[target] = handlers.get(target, ()) + callbacks
        return handlers

    async def apply(
        self, hook: Literal["inlet", "request", "stream", "outlet"], value: Any, request: Request,
        user: dict[str, Any], metadata: dict[str, Any], model: dict[str, Any],
        emitter: Callable[[dict[str, Any]], Awaitable[Any]] | None,
    ) -> Any:
        if not hasattr(request.state, "aihub_mod_runs"):
            request.state.aihub_mod_runs = {}
        key = (metadata.get("task_id"), metadata.get("chat_id"), metadata.get("message_id"))
        runs = request.state.aihub_mod_runs
        if key not in runs:
            runs[key] = asyncio.create_task(self._run(request, user, metadata, model, emitter))
        run = await runs[key]
        run.bind_task()
        return await run.apply(hook, value)

    @staticmethod
    def _view(request: Request) -> str:
        view = request.headers.get("x-aihub-mod-view")
        tenant = request.headers.get("x-aihub-mod-tenant")
        if (view is None) != (tenant is None) or (view is not None and (
            not re.fullmatch(r"[a-f0-9]{32}", view) or not 1 <= len(tenant) <= 255
        )):
            raise HTTPException(400, "Invalid mod view or tenant identifier.")
        execution = request.headers.get("x-aihub-mod-execution")
        if execution is not None and (view is None or not re.fullmatch(r"[a-f0-9]{32}", execution)):
            raise HTTPException(400, "Invalid mod execution identifier.")
        return view or uuid4().hex

    async def _snapshot(self, request: Request, user: dict[str, Any]) -> ModSnapshot:
        if not user.get("id") or not user.get("email"):
            raise HTTPException(401, "Backend mods require a verified Open WebUI user.")
        if not hasattr(request.state, "aihub_mod_snapshot"):
            request.state.aihub_mod_view = self._view(request)
            request.state.aihub_mod_snapshot = asyncio.create_task(self.host.client.configuration(
                name=user.get("name", "User"), email=user["email"],
                compatibility=self.host.compatibility,
            ))
        snapshot = await asyncio.shield(request.state.aihub_mod_snapshot)
        if request.headers.get("x-aihub-mod-tenant") not in {None, snapshot.tenant_id}:
            raise HTTPException(403, "The mod view belongs to another active tenant.")
        return snapshot

    async def handle(
        self, tenant_id: str, mod_id: str, path: str, request: Request, user: dict[str, Any],
    ) -> Any:
        snapshot = await self._snapshot(request, user)
        if snapshot.tenant_id != tenant_id:
            raise HTTPException(403, "The mod request belongs to another active tenant")
        selection = next((mod for mod in snapshot.mods if mod.enabled and mod.mod_id == mod_id), None)
        if selection is None:
            raise HTTPException(403, "This mod is not enabled for the tenant")
        request.state.aihub_mod_path = path
        overrides = await self.request_overrides(request, user)
        package, context = request.state.aihub_mod_bindings[selection.mod_id]
        # The ASGI middleware resets this after streaming/background response work completes.
        CallableRegistry.active.set(CallableRegistry.selection(overrides, getattr(request.state, "aihub_global_handlers", None)))
        return await package.handle(context)

    async def _run(
        self, request: Request, user: dict[str, Any], metadata: dict[str, Any], model: dict[str, Any],
        emitter: Callable[[dict[str, Any]], Awaitable[Any]] | None,
    ) -> ModRun:
        execution = request.headers.get("x-aihub-mod-execution")
        snapshot = await self._snapshot(request, user)
        await self.request_overrides(request, user)
        filters = []
        for selection in snapshot.mods:
            if not selection.enabled:
                continue
            package, _ = request.state.aihub_mod_bindings[selection.mod_id]
            instance = package.create_filter()
            if instance is not None:
                context = ModRunContext(
                    id=request.state.aihub_mod_view, tenant_id=snapshot.tenant_id, mod_id=selection.mod_id,
                    publication=selection.publication, execution_id=execution,
                    settings=selection.model_copy(deep=True).settings, request=request, user=dict(user),
                    metadata=dict(metadata), model=model, event_emitter=emitter,
                )
                filters.append((instance, context))
        return ModRun(filters=filters)

    async def _package(self, snapshot: ModSnapshot, publication: str, mod_id: str, user: dict[str, Any]) -> BackendPackage:
        identity = SimpleNamespace(name=user.get("name", "User"), email=user["email"])
        archive = await self.host._archive(snapshot.tenant_id, publication, identity)
        manifest = json.loads(archive.read("publication.json", manifest=True))
        revision = manifest.get("source_revision", "")
        if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{64}", revision):
            raise ValueError("Publication has no valid backend source revision")
        if manifest.get("compatibility") != json.loads(self.host.compatibility):
            raise ValueError("Backend publication belongs to another host version")
        declared = manifest.get("backend_targets", {})
        for target, fingerprint in declared.items():
            if CallableRegistry.catalog.get(target) != fingerprint:
                raise HTTPException(409, f"Backend callable changed or is absent: {target}. Republish the mod.")
        async def read_source() -> bytes:
            content = await self.host.client.request(
                "GET", snapshot.tenant_id, f"/publications/{publication}/source", name=identity.name, email=identity.email,
                compatibility=self.host.compatibility,
            )
            manifest = json.loads(BackendPackage._files(content)["mod.json"])
            if manifest.get("backend_restart_required") or "open_webui.main:lifespan" in manifest.get("backend_overrides", {}):
                raise HTTPException(409, "This backend mod requires global activation and an Open WebUI restart")
            return content

        package = await self.load_package(revision, mod_id, read_source)
        if package.restart_required:
            raise HTTPException(409, "This backend mod requires global activation and an Open WebUI restart")
        try:
            package.check_targets(declared)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        return package

    async def load_package(
        self, revision: str, mod_id: str, read_source: Callable[[], Awaitable[bytes]],
    ) -> BackendPackage:
        async with self.package_lock:
            if revision not in self.packages:
                content = await read_source()
                loading = asyncio.create_task(asyncio.to_thread(BackendPackage, revision, content, mod_id))
                try:
                    self.packages[revision] = await asyncio.shield(loading)
                except asyncio.CancelledError:
                    self.packages[revision] = await loading
                    raise
            return self.packages[revision]

    async def close(self) -> None:
        for package in self.packages.values():
            await asyncio.to_thread(package.close)
        self.packages.clear()
