from typing import ClassVar

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response


class OpenaiErrorHandler:
    """Errors the platform raises itself on the OpenAI-compatible routes, in OpenAI's error format.

    The OpenAI SDKs read only `error.message`, and a request they consider malformed is a 400, not FastAPI's 422.
    `detail` stays next to it, as on gateway errors, because the platform's own clients read that. Every other route
    keeps FastAPI's default responses.
    """

    ROUTE_MARKER: ClassVar[str] = "/openai/"
    ERROR_TYPES: ClassVar[dict[int, str]] = {
        status.HTTP_400_BAD_REQUEST: "invalid_request_error",
        status.HTTP_401_UNAUTHORIZED: "authentication_error",
        status.HTTP_403_FORBIDDEN: "permission_error",
        status.HTTP_404_NOT_FOUND: "not_found_error",
        status.HTTP_413_CONTENT_TOO_LARGE: "invalid_request_error",
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "invalid_request_error",
        status.HTTP_422_UNPROCESSABLE_CONTENT: "invalid_request_error",
        status.HTTP_429_TOO_MANY_REQUESTS: "rate_limit_error",
    }

    @staticmethod
    def register(app: FastAPI) -> None:
        app.add_exception_handler(HTTPException, OpenaiErrorHandler.handle_http_error)
        app.add_exception_handler(RequestValidationError, OpenaiErrorHandler.handle_validation_error)

    @staticmethod
    async def handle_http_error(request: Request, exception: HTTPException) -> Response:
        if OpenaiErrorHandler.ROUTE_MARKER not in request.url.path:
            return await http_exception_handler(request, exception)
        return OpenaiErrorHandler.response(
            exception.status_code,
            OpenaiErrorHandler.message_of(exception.detail),
            detail=exception.detail,
            headers=exception.headers,
        )

    @staticmethod
    def message_of(detail: object) -> str:
        """A detail may be structured, as the usage limit's is; its own message is what the caller should read."""
        if isinstance(detail, dict) and isinstance(detail.get("message"), str):
            return detail["message"]
        return str(detail)

    @staticmethod
    async def handle_validation_error(request: Request, exception: RequestValidationError) -> Response:
        if OpenaiErrorHandler.ROUTE_MARKER not in request.url.path:
            return await request_validation_exception_handler(request, exception)
        errors = jsonable_encoder(exception.errors())
        first = errors[0] if errors else {}
        location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
        message = f"{location}: {first.get('msg')}" if location else str(first.get("msg", "Invalid request."))
        return OpenaiErrorHandler.response(status.HTTP_400_BAD_REQUEST, message, param=location or None, detail=errors)

    @staticmethod
    def response(
        status_code: int,
        message: str,
        *,
        param: str | None = None,
        detail: object = None,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        fallback_type = "server_error" if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR else "api_error"
        error_type = OpenaiErrorHandler.ERROR_TYPES.get(status_code, fallback_type)
        return JSONResponse(
            status_code=status_code,
            content={
                "detail": message if detail is None else detail,
                "error": {"message": message, "type": error_type, "param": param, "code": status_code},
            },
            headers=headers,
        )
