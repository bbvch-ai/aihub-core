import inspect
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request

from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.mod_runtime import ModRuntime
from aihub_mods.mod_scope_middleware import ModScopeMiddleware


class ModAuthentication:
    TARGET = "open_webui.utils.auth:get_current_user"

    def __init__(self, runtime: ModRuntime) -> None:
        self.runtime = runtime

    def install(self, app: FastAPI) -> None:
        from open_webui.utils.auth import get_current_user

        expected = ["request", "response", "background_tasks", "auth_token"]
        if not inspect.iscoroutinefunction(get_current_user) or list(inspect.signature(get_current_user).parameters) != expected:
            raise RuntimeError("Open WebUI authentication changed; review the mod request-scope adapter")
        CallableRegistry.system_handlers = {**CallableRegistry.system_handlers, self.TARGET: (self.authenticate,)}
        app.add_middleware(ModScopeMiddleware)

    async def authenticate(self, next: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        user = await next(*args, **kwargs)
        request: Request = kwargs["request"] if "request" in kwargs else args[0]
        if request.url.path.startswith("/_aihub/mods/") or user.role not in {"user", "admin"}:
            return user
        # Stopping existing work must not depend on loading a newly selected mod.
        if request.method == "POST" and (
            request.url.path.startswith("/api/tasks/stop/")
            or (request.url.path.startswith("/api/tasks/chat/") and request.url.path.endswith("/stop"))
        ):
            return user
        if not request.headers.get("x-aihub-mod-view") and request.url.path != "/api/chat/completions":
            return user
        identity = {key: getattr(user, key) for key in ("id", "name", "email", "role")}
        tenant = await self.runtime.request_overrides(request, identity)
        global_handlers = getattr(request.state, "aihub_global_handlers", None)
        CallableRegistry.active.set(CallableRegistry.selection(tenant, global_handlers))
        return user
