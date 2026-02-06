import logging
import traceback

from aiohttp import (
    TraceRequestEndParams,
    TraceRequestExceptionParams,
    TraceRequestStartParams,
)
from fastapi import status
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.httpx import (
    HTTPXClientInstrumentor,
    RequestInfo,
    ResponseInfo,
)
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.milvus import MilvusInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Span, StatusCode
from redis.asyncio import Redis
from requests import PreparedRequest, Response

logger = logging.getLogger(__name__)


class CustomSpanAttributes(SpanAttributes):
    DB_INSTANCE = "db.instance"
    DB_TYPE = "db.type"
    DB_IP = "db.ip"
    DB_PORT = "db.port"
    ERROR_KIND = "error.kind"
    ERROR_OBJECT = "error.object"
    ERROR_MESSAGE = "error.message"
    RESULT_CODE = "result.code"
    RESULT_MESSAGE = "result.message"
    RESULT_ERRORS = "result.errors"


def requests_hook(span: Span, request: PreparedRequest):
    span.update_name(f"{request.method} {request.url}")
    span.set_attributes(
        attributes={
            CustomSpanAttributes.HTTP_URL: request.url,
            CustomSpanAttributes.HTTP_METHOD: request.method,
        }
    )


def response_hook(span: Span, request: PreparedRequest, response: Response):
    span.set_attributes(
        attributes={
            CustomSpanAttributes.HTTP_STATUS_CODE: response.status_code,
        }
    )
    span.set_status(StatusCode.ERROR if response.status_code >= 400 else StatusCode.OK)


def redis_request_hook(span: Span, instance: Redis, *args, **kwargs):
    try:
        connection_kwargs: dict = instance.connection_pool.connection_kwargs
        host = connection_kwargs.get("host")
        port = connection_kwargs.get("port")
        db = connection_kwargs.get("db")
        span.set_attributes(
            {
                CustomSpanAttributes.DB_INSTANCE: f"{host}/{db}",
                CustomSpanAttributes.DB_NAME: f"{host}/{db}",
                CustomSpanAttributes.DB_TYPE: "redis",
                CustomSpanAttributes.DB_PORT: port,
                CustomSpanAttributes.DB_IP: host,
                CustomSpanAttributes.DB_STATEMENT: " ".join([str(i) for i in args]),
                CustomSpanAttributes.DB_OPERATION: str(args[0]),
            }
        )
    except Exception:  # pylint: disable=W0718
        logger.error(traceback.format_exc())


def httpx_request_hook(span: Span, request: RequestInfo):
    span.update_name(f"{request.method.decode()} {str(request.url)}")
    span.set_attributes(
        attributes={
            CustomSpanAttributes.HTTP_URL: str(request.url),
            CustomSpanAttributes.HTTP_METHOD: request.method.decode(),
        }
    )


def httpx_response_hook(span: Span, request: RequestInfo, response: ResponseInfo):
    span.set_attribute(CustomSpanAttributes.HTTP_STATUS_CODE, response.status_code)
    span.set_status(StatusCode.ERROR if response.status_code >= status.HTTP_400_BAD_REQUEST else StatusCode.OK)


async def httpx_async_request_hook(span: Span, request: RequestInfo):
    httpx_request_hook(span, request)


async def httpx_async_response_hook(span: Span, request: RequestInfo, response: ResponseInfo):
    httpx_response_hook(span, request, response)


def aiohttp_request_hook(span: Span, request: TraceRequestStartParams):
    span.update_name(f"{request.method} {str(request.url)}")
    span.set_attributes(
        attributes={
            CustomSpanAttributes.HTTP_URL: str(request.url),
            CustomSpanAttributes.HTTP_METHOD: request.method,
        }
    )


def aiohttp_response_hook(span: Span, response: TraceRequestExceptionParams | TraceRequestEndParams):
    if isinstance(response, TraceRequestEndParams):
        span.set_attribute(CustomSpanAttributes.HTTP_STATUS_CODE, response.response.status)
        span.set_status(StatusCode.ERROR if response.response.status >= status.HTTP_400_BAD_REQUEST else StatusCode.OK)
    elif isinstance(response, TraceRequestExceptionParams):
        span.set_status(StatusCode.ERROR)
        span.set_attribute(CustomSpanAttributes.ERROR_MESSAGE, str(response.exception))


class AihubInstrumentor(BaseInstrumentor):
    """
    Custom instrumentor for the application that instruments all required libraries.
    Follows the OpenTelemetry BaseInstrumentor pattern for proper lifecycle management.
    """

    def instrumentation_dependencies(self) -> list[str]:
        """
        Return a list of instrumentation dependencies.
        This can be used to ensure certain packages are installed.
        """
        return []

    def _instrument(self, **kwargs):
        """
        Instrument all the libraries used by the application.
        This method is idempotent - calling it multiple times has no effect.
        """
        logger.info("🔍 Starting application instrumentation...")

        from aihub_lib.infrastructure.opentelemetry.OpenTelemetrySettings import OpenTelemetrySettings

        otel_settings = OpenTelemetrySettings()

        if not otel_settings.ENABLED:
            logger.info("OpenTelemetry instrumentation disabled: OTEL_ENABLED=False")
            return

        # Instrument async operations
        AsyncioInstrumentor().instrument()

        # Instrument databases
        PymongoInstrumentor().instrument()
        MilvusInstrumentor().instrument()
        RedisInstrumentor().instrument(request_hook=redis_request_hook)

        # Instrument HTTP clients
        RequestsInstrumentor().instrument(request_hook=requests_hook, response_hook=response_hook)
        HTTPXClientInstrumentor().instrument(
            request_hook=httpx_request_hook,
            response_hook=httpx_response_hook,
            async_request_hook=httpx_async_request_hook,
            async_response_hook=httpx_async_response_hook,
        )
        AioHttpClientInstrumentor().instrument(
            request_hook=aiohttp_request_hook,
            response_hook=aiohttp_response_hook,
        )

        # Instrument other libraries
        Jinja2Instrumentor().instrument()
        BotocoreInstrumentor().instrument()
        LlamaIndexInstrumentor().instrument()
        LoggingInstrumentor().instrument()

        # Configure the tracing and logging providers
        otel_settings.configure_tracing()
        otel_settings.configure_logging()

        logger.info("✅ Application instrumentation completed")

    def _uninstrument(self, **kwargs):
        """
        Uninstrument all the libraries.
        This allows for clean shutdown and re-instrumentation if needed.
        """
        logger.info("🔍 Uninstrumenting application...")

        AsyncioInstrumentor().uninstrument()
        PymongoInstrumentor().uninstrument()
        MilvusInstrumentor().uninstrument()
        RedisInstrumentor().uninstrument()
        RequestsInstrumentor().uninstrument()
        HTTPXClientInstrumentor().uninstrument()
        AioHttpClientInstrumentor().uninstrument()
        Jinja2Instrumentor().uninstrument()
        BotocoreInstrumentor().uninstrument()
        LlamaIndexInstrumentor().uninstrument()
        LoggingInstrumentor().uninstrument()

        logger.info("✅ Application uninstrumentation completed")
