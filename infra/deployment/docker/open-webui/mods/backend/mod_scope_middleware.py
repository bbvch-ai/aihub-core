from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import JSONResponse

from aihub_mods.callable_registry import CallableRegistry


class ModScopeMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope.get("path", "")
        management = path.startswith("/_aihub/mods/") and not path.startswith("/_aihub/mods/tenants/")
        host = getattr(scope["app"].state, "aihub_mods", None)
        runtime = host.global_runtime if host is not None else None
        if runtime is not None and runtime.error and not management:
            await JSONResponse({
                "detail": "Chat customizations could not be loaded. Please contact your administrator."
            }, status_code=503)(scope, receive, send)
            return
        global_handlers = {} if management else runtime.handlers(Request(scope)) if runtime else dict(CallableRegistry.global_handlers)
        scope.setdefault("state", {})["aihub_global_handlers"] = global_handlers
        token = CallableRegistry.active.set(global_handlers)
        try:
            await self.app(scope, receive, send)
        finally:
            CallableRegistry.active.reset(token)
