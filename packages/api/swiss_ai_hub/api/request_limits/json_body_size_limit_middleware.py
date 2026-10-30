from fastapi import HTTPException, status
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class JsonBodySizeLimitMiddleware:
    """Rejects a JSON body past the limit while it arrives, before anything parses it.

    The API runs a single worker, and a parsed JSON body sits in memory several times over (the bytes, the decoded
    objects, the validated model), so one oversized request would stall or exhaust it for every other caller.
    Multipart and binary uploads are left to their endpoints, which stream and bound them themselves.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self._is_json(Headers(scope=scope)):
            await self.app(scope, receive, send)
            return
        content_length = Headers(scope=scope).get("content-length", "")
        if content_length.isdigit() and int(content_length) > self.max_bytes:
            await JSONResponse({"detail": self._detail()}, status.HTTP_413_CONTENT_TOO_LARGE)(scope, receive, send)
            return
        await self.app(scope, self._bounded(receive), send)

    def _bounded(self, receive: Receive) -> Receive:
        """Counts what a chunked body, which announces no length, actually delivers."""
        received = 0

        async def bounded_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, self._detail())
            return message

        return bounded_receive

    def _detail(self) -> str:
        return f"The request body is larger than the {self.max_bytes} bytes a JSON request may have."

    @staticmethod
    def _is_json(headers: Headers) -> bool:
        media_type = headers.get("content-type", "").split(";")[0].strip().lower()
        return media_type == "application/json" or media_type.endswith("+json")
