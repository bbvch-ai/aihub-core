import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_error import OpenTerminalError

logger = logging.getLogger(__name__)


class OpenTerminalErrorHandler:
    """Hands a refusal of the code sandbox to the caller with its reason; anything else is the sandbox failing."""

    CALLER_ERRORS = frozenset({400, 403, 404, 409, 413})
    BAD_GATEWAY = 502

    @staticmethod
    def register(app: FastAPI) -> None:
        app.add_exception_handler(OpenTerminalError, OpenTerminalErrorHandler.handle)

    @staticmethod
    async def handle(request: Request, exception: OpenTerminalError) -> JSONResponse:
        if exception.status_code in OpenTerminalErrorHandler.CALLER_ERRORS:
            return JSONResponse(status_code=exception.status_code, content={"detail": str(exception)})
        logger.error(f"Code sandbox failed for {request.method} {request.url.path}: {exception}")
        return JSONResponse(
            status_code=OpenTerminalErrorHandler.BAD_GATEWAY, content={"detail": "The code sandbox did not respond."}
        )
