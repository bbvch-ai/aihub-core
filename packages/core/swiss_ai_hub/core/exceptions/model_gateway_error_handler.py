import logging
from typing import Any, ClassVar

from fastapi import FastAPI
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAIError
from opentelemetry.trace import Status, StatusCode, get_current_span
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ModelGatewayErrorHandler:
    """
    Turns LiteLLM and model-provider failures into responses that name their cause.

    Every model call goes through the OpenAI SDK, whose errors are not ``HTTPException``.
    Unhandled, they left the app as Starlette's plain-text 500: the caller learned nothing
    (OpenWebUI could only report "500 Server Error ... Internal Server Error"), and the only
    record naming the cause was the ASGI server's traceback, which never left the container.
    Both are resolved here, at the HTTP boundary that owns protocol conversion.

    Registered by ``Runner`` so it covers any app built from that base, not just the main API. It
    fires only for exceptions that actually reach the boundary: ``BaseChatBot`` catches its own, so
    the bot's chat path keeps translating them in-route instead.
    """

    BAD_GATEWAY = 502
    GATEWAY_TIMEOUT = 504
    # Above this an upstream failure repeats on every request, so its traceback stops being
    # information and becomes volume.
    SERVER_ERROR_FLOOR = 500

    # Statuses a caller can act on, because its own request was rejected. Every other upstream
    # status is this deployment's configuration failing rather than the request: 401/403 is a
    # mis-set provider key and 404 a model missing at the provider, and reporting either
    # verbatim would send clients chasing credentials they never supplied.
    CALLER_ACTIONABLE_STATUSES: ClassVar[frozenset[int]] = frozenset({400, 413, 422, 429})
    UPSTREAM_TIMEOUT_STATUSES: ClassVar[frozenset[int]] = frozenset({408, 504})

    # Failures an operator cannot act on: a request too large or malformed for the provider, and a
    # rate limit. Note 400 is deliberately absent — passing an upstream status through means that
    # bucket also carries this deployment's own faults (a model name or parameter it got wrong),
    # which is the very incident this handler exists for.
    NON_ACTIONABLE_STATUSES: ClassVar[frozenset[int]] = frozenset({413, 422, 429})

    @staticmethod
    def register(app: FastAPI) -> None:
        """``APITimeoutError`` subclasses ``APIConnectionError``, and every concrete status
        error subclasses ``APIStatusError``; Starlette resolves handlers along the exception's
        MRO, so the most specific registration wins and ``OpenAIError`` only catches the rest.

        That base registration is not belt-and-braces. Several members of the family are siblings
        of ``APIStatusError`` rather than subclasses — ``APIResponseValidationError`` sits directly
        under ``APIError``, and ``LengthFinishReasonError`` / ``ContentFilterFinishReasonError``
        directly under ``OpenAIError`` — so without it a response body LiteLLM shaped wrongly, the
        exact failure class this handler exists for, still left the app as an opaque 500.
        """
        app.add_exception_handler(APIStatusError, ModelGatewayErrorHandler.handle_status_error)
        app.add_exception_handler(APITimeoutError, ModelGatewayErrorHandler.handle_timeout_error)
        app.add_exception_handler(APIConnectionError, ModelGatewayErrorHandler.handle_connection_error)
        app.add_exception_handler(OpenAIError, ModelGatewayErrorHandler.handle_gateway_error)

    @staticmethod
    async def handle_gateway_error(request: Request, exception: OpenAIError) -> JSONResponse:
        """The backstop for everything in the family that carries no HTTP status of its own.

        Logged with a traceback deliberately: unlike a provider outage these are unclassified, so
        the call site is the only thing that says which of them happened and where.
        """
        logger.exception(
            f"Model gateway raised {type(exception).__name__} for {request.method} {request.url.path}: {exception}"
        )
        return ModelGatewayErrorHandler._failure_response(
            status_code=ModelGatewayErrorHandler.BAD_GATEWAY,
            message=str(exception),
            upstream_status=None,
            exception=exception,
        )

    @staticmethod
    async def handle_status_error(request: Request, exception: APIStatusError) -> JSONResponse:
        message = ModelGatewayErrorHandler._upstream_message(exception)
        ModelGatewayErrorHandler._log_status_error(request, exception.status_code, message)
        return ModelGatewayErrorHandler._failure_response(
            status_code=ModelGatewayErrorHandler._caller_facing_status(exception.status_code),
            message=message,
            upstream_status=exception.status_code,
            exception=exception,
        )

    @staticmethod
    async def handle_timeout_error(request: Request, exception: APITimeoutError) -> JSONResponse:
        # No traceback: a timeout repeats on every request while the gateway is slow, and the stack
        # is our own call site either way — record 5000 says nothing record 1 did not. The span
        # still carries the exception for the one case where the call site matters.
        logger.error(f"Model gateway timed out for {request.method} {request.url.path}")
        return ModelGatewayErrorHandler._failure_response(
            status_code=ModelGatewayErrorHandler.GATEWAY_TIMEOUT,
            message="The model gateway did not respond in time.",
            upstream_status=None,
            exception=exception,
        )

    @staticmethod
    async def handle_connection_error(request: Request, exception: APIConnectionError) -> JSONResponse:
        # No traceback, for the same reason as the timeout: an unreachable gateway fails every
        # request, and the traceback of a connection error carries nothing the message does not.
        logger.error(f"Model gateway unreachable for {request.method} {request.url.path}")
        return ModelGatewayErrorHandler._failure_response(
            status_code=ModelGatewayErrorHandler.BAD_GATEWAY,
            message="The model gateway is unreachable.",
            upstream_status=None,
            exception=exception,
        )

    @staticmethod
    def _log_status_error(request: Request, upstream_status: int, message: str) -> None:
        """Three levels of noise, chosen by who must act and by whether the failure repeats.

        ERROR is what an operator is expected to act on, which is why a 4xx does not automatically
        stay below it: the request failed either way, but only some of these failures are this
        deployment's to fix. The ones that are not say nothing actionable, and a traceback per
        rejected request would flood the pipeline during a rate-limit storm — when its volume is
        already worst.

        The traceback is a separate axis from the level. A provider outage returns 5xx on *every*
        request, so its stack is as repetitive as a rate limit's even though an operator does need
        to know: ERROR, no traceback. A 401/403/404/400 happens once per misconfiguration and the
        call site is what identifies it, so those keep the traceback.
        """
        summary = f"Model gateway returned {upstream_status} for {request.method} {request.url.path}: {message}"

        if upstream_status in ModelGatewayErrorHandler.NON_ACTIONABLE_STATUSES:
            logger.warning(summary)
        elif upstream_status >= ModelGatewayErrorHandler.SERVER_ERROR_FLOOR:
            logger.error(summary)
        else:
            logger.exception(summary)

    @staticmethod
    def _caller_facing_status(upstream_status: int) -> int:
        if upstream_status in ModelGatewayErrorHandler.CALLER_ACTIONABLE_STATUSES:
            return upstream_status
        if upstream_status in ModelGatewayErrorHandler.UPSTREAM_TIMEOUT_STATUSES:
            return ModelGatewayErrorHandler.GATEWAY_TIMEOUT
        return ModelGatewayErrorHandler.BAD_GATEWAY

    @staticmethod
    def cause_of(exception: Exception) -> str:
        """The gateway's own description of a failure, for callers outside the HTTP boundary.

        Agent steps fail through the same SDK but report through NATS and logs rather than a
        response, and ``str(exception)`` there is the SDK's ``Error code: N - {…}`` wrapper — the
        cause is inside it, so it is searchable but not readable, and it reaches the chat UI that
        way too. Anything that is not a gateway error is returned unchanged.
        """
        if isinstance(exception, APIStatusError):
            return ModelGatewayErrorHandler._upstream_message(exception)
        return str(exception)

    @staticmethod
    def _upstream_message(exception: APIStatusError) -> str:
        """Unwraps the OpenAI error envelope, whose ``error.message`` is what actually names the
        cause ("Invalid model name passed in model=..."). ``exception.message`` only wraps that
        same body in "Error code: N - {...}"."""
        body: Any = exception.body
        nested = body.get("error") if isinstance(body, dict) else None

        if isinstance(nested, dict) and nested.get("message"):
            return str(nested["message"])
        if isinstance(nested, str):
            return nested
        return exception.message

    @staticmethod
    def _failure_response(
        *, status_code: int, message: str, upstream_status: int | None, exception: Exception
    ) -> JSONResponse:
        """The message is carried under both keys deliberately: this platform's own clients read
        FastAPI's ``detail``, while the OpenAI-compatible clients this API emulates (OpenWebUI,
        the OpenAI SDKs) only ever read ``error.message``. Dropping either one hides the cause
        from one of the two."""
        ModelGatewayErrorHandler._mark_span_failed(exception)

        return JSONResponse(
            status_code=status_code,
            content={
                "detail": message,
                "error": {"message": message, "type": "model_gateway_error", "code": upstream_status},
            },
        )

    @staticmethod
    def _mark_span_failed(exception: Exception) -> None:
        """The FastAPI instrumentation marks the server span from an exception that propagates out
        of the middleware stack. A handled one never does — ``ExceptionMiddleware`` converts it to
        a response below that point — so nothing else marks this span. The instrumentation's status
        setter still runs afterwards but cannot undo this: the SDK ignores a set_status back to
        UNSET, which is what it derives from the 4xx this handler may return."""
        span = get_current_span()
        span.set_attribute("error.type", type(exception).__name__)
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))
