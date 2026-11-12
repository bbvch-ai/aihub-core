from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class FrontendCache:
    ENTRIES = {
        "/_aihub/mods/host.js", "/_aihub/mods/runtime.js", "/_aihub/mods/compatibility.json",
    }

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        document = Headers(scope=scope).get("sec-fetch-dest") in {"document", "iframe"}

        async def send_response(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                # Stable entry URLs must not retain imports from an older image build.
                if document or scope["path"] in self.ENTRIES or headers.get("content-type", "").startswith("text/html"):
                    policy = headers.get("cache-control", "")
                    directives = {part.strip().lower() for part in policy.split(",")}
                    if not directives.intersection({"no-cache", "no-store"}):
                        headers["Cache-Control"] = f"{policy}, no-cache" if policy else "no-cache"
            await send(message)

        await self.app(scope, receive, send_response)
