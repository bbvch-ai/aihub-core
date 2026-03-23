from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import HTTPException, Request


def use_limited_body(max_bytes: int) -> Callable[[Request], Coroutine[Any, Any, bytes]]:
    """Create a dependency that streams the request body and rejects if it exceeds max_bytes."""

    async def _read_body(request: Request) -> bytes:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > max_bytes:
            raise HTTPException(
                status_code=413, detail=f"File too large: Content-Length exceeds {max_bytes} byte limit"
            )

        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > max_bytes:
                raise HTTPException(status_code=413, detail=f"File too large: exceeds {max_bytes} byte limit")
        return bytes(body)

    return _read_body
