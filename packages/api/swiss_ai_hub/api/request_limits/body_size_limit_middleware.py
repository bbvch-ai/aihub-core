from fastapi import HTTPException, status
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodySizeLimitMiddleware:
    """Rejects a request body past the limit while it arrives, before anything reads it whole.

    FastAPI reads the full body of every endpoint that takes one, whatever its content type, so the bound applies to all
    bodies: limiting only JSON would let a caller pass any other type, or none, and still be buffered. The API runs a
    single worker, so one oversized body would stall or exhaust it for every other caller. Multipart uploads are spooled
    to disk by Starlette, and the exempt paths stream and bound their bodies themselves.
    """

    def __init__(self, app: ASGIApp, max_bytes: int, exempt_path_suffixes: tuple[str, ...] = ()) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.exempt_path_suffixes = exempt_path_suffixes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or self._is_exempt(scope):
            await self.app(scope, receive, send)
            return
        content_length = Headers(scope=scope).get("content-length", "")
        if content_length.isdigit() and int(content_length) > self.max_bytes:
            await JSONResponse({"detail": self._detail()}, status.HTTP_413_CONTENT_TOO_LARGE)(scope, receive, send)
            return
        await self.app(scope, self._bounded(receive), send)

    def _is_exempt(self, scope: Scope) -> bool:
        media_type = Headers(scope=scope).get("content-type", "").split(";")[0].strip().lower()
        return media_type == "multipart/form-data" or scope["path"].endswith(self.exempt_path_suffixes)

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
        return f"The request body is larger than the {self.max_bytes} bytes a request may have."
