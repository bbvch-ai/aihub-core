from fastapi import HTTPException, params, status
from fastapi.routing import APIRoute
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodySizeLimitMiddleware:
    """Rejects a request body past the limit while it arrives, before anything reads it whole.

    FastAPI reads the full body of every endpoint that takes one, whatever its content type, so the bound applies to all
    bodies: limiting only JSON would let a caller pass any other type, or none, and still be buffered. The API runs a
    single worker, so one oversized body would stall or exhaust it for every other caller. Only a form upload to a route
    that parses a form skips it, since Starlette spools the form's files to disk; the caller's `multipart/form-data`
    label alone does not, because a route that takes no form reads the body whole whatever it is labelled. The exempt
    paths stream and bound their bodies themselves.
    """

    def __init__(self, app: ASGIApp, max_bytes: int, exempt_path_suffixes: tuple[str, ...] = ()) -> None:
        self.app = app
        self.max_bytes = max_bytes
        self.exempt_path_suffixes = exempt_path_suffixes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"].endswith(self.exempt_path_suffixes):
            await self.app(scope, receive, send)
            return
        content_length = Headers(scope=scope).get("content-length", "")
        if not self._labelled_multipart(scope) and content_length.isdigit() and int(content_length) > self.max_bytes:
            await JSONResponse({"detail": self._detail()}, status.HTTP_413_CONTENT_TOO_LARGE)(scope, receive, send)
            return
        await self.app(scope, self._bounded(scope, receive), send)

    def _bounded(self, scope: Scope, receive: Receive) -> Receive:
        """Counts what the body actually delivers, which a chunked body does not announce.

        Whether the request is a form upload is decided on the first read: an endpoint reads its body only after
        routing has put the matched route into the scope, while the middleware runs before any route is known.
        """
        received = 0

        async def bounded_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request" and not self._is_form_upload(scope):
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, self._detail())
            return message

        return bounded_receive

    def _is_form_upload(self, scope: Scope) -> bool:
        route = scope.get("route")
        return (
            self._labelled_multipart(scope)
            and isinstance(route, APIRoute)
            and route.body_field is not None
            and isinstance(route.body_field.field_info, params.Form)
        )

    @staticmethod
    def _labelled_multipart(scope: Scope) -> bool:
        return Headers(scope=scope).get("content-type", "").split(";")[0].strip().lower() == "multipart/form-data"

    def _detail(self) -> str:
        return f"The request body is larger than the {self.max_bytes} bytes a request may have."
