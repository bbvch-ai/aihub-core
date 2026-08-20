import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from openai import APIConnectionError, APIStatusError, APITimeoutError, BadRequestError
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode
from starlette.requests import Request

from swiss_ai_hub.core.exceptions.model_gateway_error_handler import ModelGatewayErrorHandler
from swiss_ai_hub.core.runners.runner import Runner

pytestmark = pytest.mark.unit

BASE_URL = "http://test"
UPSTREAM_URL = "http://litellm:4000/audio/transcriptions"

# The message LiteLLM actually returned for issue "Invalid model name", nested exactly as the
# OpenAI error envelope nests it.
UPSTREAM_MESSAGE = (
    "litellm.BadRequestError: OpenAIException - /audio/transcriptions: "
    "Invalid model name passed in model=whisper-large-v3."
)
UPSTREAM_BODY = {"error": {"message": UPSTREAM_MESSAGE, "type": None, "param": None, "code": "400"}}


def _status_error(status_code: int, body: dict | str | None = None) -> APIStatusError:
    request = httpx.Request("POST", UPSTREAM_URL)
    response = httpx.Response(status_code, request=request, json=body if body is not None else {})
    return APIStatusError(f"Error code: {status_code}", response=response, body=body)


def _fake_request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/openai/audio/transcriptions", "headers": []})


class TestUpstreamStatusIsTranslatedForTheCaller:
    """A caller may only be handed a status it can act on; a provider key or model name that this
    deployment got wrong must not arrive as the caller's own 401/404."""

    @pytest.mark.parametrize(("upstream", "expected"), [(400, 400), (413, 413), (422, 422), (429, 429)])
    def test_caller_actionable_statuses_pass_through(self, upstream: int, expected: int):
        assert ModelGatewayErrorHandler._caller_facing_status(upstream) == expected

    @pytest.mark.parametrize("upstream", [401, 403, 404, 500, 502, 503])
    def test_deployment_faults_become_bad_gateway(self, upstream: int):
        assert ModelGatewayErrorHandler._caller_facing_status(upstream) == ModelGatewayErrorHandler.BAD_GATEWAY

    @pytest.mark.parametrize("upstream", [408, 504])
    def test_upstream_timeouts_become_gateway_timeout(self, upstream: int):
        assert ModelGatewayErrorHandler._caller_facing_status(upstream) == ModelGatewayErrorHandler.GATEWAY_TIMEOUT


class TestUpstreamMessageIsUnwrapped:
    def test_nested_openai_envelope_message_is_used(self):
        assert ModelGatewayErrorHandler._upstream_message(_status_error(400, UPSTREAM_BODY)) == UPSTREAM_MESSAGE

    def test_plain_string_error_is_used(self):
        assert ModelGatewayErrorHandler._upstream_message(_status_error(400, {"error": "no capacity"})) == "no capacity"

    def test_unrecognized_body_falls_back_to_sdk_message(self):
        assert ModelGatewayErrorHandler._upstream_message(_status_error(500, {"unexpected": 1})) == "Error code: 500"


class TestFailureResponseNamesTheCause:
    @pytest.mark.asyncio
    async def test_both_error_envelopes_carry_the_message(self):
        response = await ModelGatewayErrorHandler.handle_status_error(
            _fake_request(), _status_error(400, UPSTREAM_BODY)
        )

        assert response.status_code == 400
        body = response.body.decode()
        assert UPSTREAM_MESSAGE in body
        assert '"detail"' in body
        assert '"error"' in body

    @pytest.mark.asyncio
    async def test_timeout_reports_gateway_timeout(self):
        exception = APITimeoutError(request=httpx.Request("POST", UPSTREAM_URL))

        response = await ModelGatewayErrorHandler.handle_timeout_error(_fake_request(), exception)

        assert response.status_code == ModelGatewayErrorHandler.GATEWAY_TIMEOUT

    @pytest.mark.asyncio
    async def test_connection_failure_reports_bad_gateway(self):
        exception = APIConnectionError(request=httpx.Request("POST", UPSTREAM_URL))

        response = await ModelGatewayErrorHandler.handle_connection_error(_fake_request(), exception)

        assert response.status_code == ModelGatewayErrorHandler.BAD_GATEWAY


class TestLogSeverityFollowsWhoMustAct:
    """The ERROR record is the only thing that reaches the log pipeline for these failures, so its
    level decides what an operator ever sees. The span marks every one of them; the log level says
    which of them somebody is expected to do something about."""

    @staticmethod
    async def _handle(upstream_status: int) -> None:
        """Raised and caught so the handler sees the live exception context Starlette gives it,
        which is what decides whether a traceback ends up on the record."""
        try:
            raise _status_error(upstream_status, UPSTREAM_BODY)
        except APIStatusError as exception:
            await ModelGatewayErrorHandler.handle_status_error(_fake_request(), exception)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("upstream", [400, 401, 404, 500, 503])
    async def test_deployment_faults_log_error_with_traceback(self, caplog, upstream: int):
        with caplog.at_level(logging.DEBUG):
            await self._handle(upstream)

        record = caplog.records[-1]
        assert record.levelno == logging.ERROR
        assert record.exc_info[0] is APIStatusError
        assert UPSTREAM_MESSAGE in record.getMessage()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("upstream", [413, 422, 429])
    async def test_non_actionable_failures_log_warning_without_traceback(self, caplog, upstream: int):
        with caplog.at_level(logging.DEBUG):
            await self._handle(upstream)

        record = caplog.records[-1]
        assert record.levelno == logging.WARNING
        assert record.exc_info is None
        assert UPSTREAM_MESSAGE in record.getMessage()


class TestHandledFailureStaysVisibleInTracing:
    """Handling the exception is what made these requests invisible in tracing: it never reaches
    the instrumentation's exception branch. The 4xx case is the one that matters — the
    instrumentation derives UNSET from it afterwards."""

    @pytest.mark.asyncio
    async def test_span_is_marked_error_for_a_passed_through_4xx(self):
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        with provider.get_tracer("test").start_as_current_span("POST /openai/audio/transcriptions"):
            await ModelGatewayErrorHandler.handle_status_error(_fake_request(), _status_error(400, UPSTREAM_BODY))

        span = exporter.get_finished_spans()[0]
        assert span.status.status_code is StatusCode.ERROR
        assert span.attributes["error.type"] == "APIStatusError"
        assert [event.name for event in span.events] == ["exception"]


class _MinimalRunner(Runner):
    @property
    def lifetime_manager(self) -> Callable[[FastAPI], AbstractAsyncContextManager]:
        raise NotImplementedError


class TestEveryRunnerRegistersTheHandler:
    """Registration lives in the base runner, so any app built from it is covered without each
    service repeating it — and losing it would silently restore the opaque 500 on every route that
    does let the exception reach the boundary."""

    def test_base_runner_registers_every_gateway_error(self):
        handlers = _MinimalRunner()._api_app.exception_handlers

        assert handlers[APIStatusError] == ModelGatewayErrorHandler.handle_status_error
        assert handlers[APITimeoutError] == ModelGatewayErrorHandler.handle_timeout_error
        assert handlers[APIConnectionError] == ModelGatewayErrorHandler.handle_connection_error


class TestHandlerIsReachedThroughTheAppStack:
    """Starlette resolves handlers along the exception's MRO, so the concrete SDK errors
    (BadRequestError and friends) must reach the base-class registration."""

    @pytest.mark.asyncio
    async def test_bad_request_error_from_an_endpoint_becomes_a_named_400(self):
        app = FastAPI()
        ModelGatewayErrorHandler.register(app)

        @app.get("/transcribe")
        async def transcribe() -> None:
            raise BadRequestError(
                "Error code: 400",
                response=httpx.Response(400, request=httpx.Request("POST", UPSTREAM_URL), json=UPSTREAM_BODY),
                body=UPSTREAM_BODY,
            )

        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.get("/transcribe")

        assert response.status_code == 400
        assert response.json()["error"]["message"] == UPSTREAM_MESSAGE
        assert response.json()["detail"] == UPSTREAM_MESSAGE
