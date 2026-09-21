import logging

import pytest
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler

from swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings import OpenTelemetrySettings

pytestmark = pytest.mark.unit

UVICORN_ERROR_LOGGER = "uvicorn.error"


def _handler() -> LoggingHandler:
    return LoggingHandler(level=logging.NOTSET, logger_provider=LoggerProvider())


def _otel_handlers(logger: logging.Logger) -> list[logging.Handler]:
    return [handler for handler in logger.handlers if isinstance(handler, LoggingHandler)]


class TestServerLoggersReachTheOtlpExporter:
    """gunicorn's UvicornWorker re-parents these loggers and sets propagate=False, so the root
    handler never saw "Exception in ASGI application" — the only record carrying the traceback of
    an unhandled 500."""

    def test_non_propagating_server_logger_gets_the_handler(self):
        server_logger = logging.getLogger(UVICORN_ERROR_LOGGER)
        original_propagate = server_logger.propagate
        server_logger.propagate = False
        try:
            OpenTelemetrySettings._attach_to_server_loggers(_handler())
            assert len(_otel_handlers(server_logger)) == 1
        finally:
            server_logger.handlers = [h for h in server_logger.handlers if not isinstance(h, LoggingHandler)]
            server_logger.propagate = original_propagate

    def test_propagating_server_logger_is_left_alone(self):
        server_logger = logging.getLogger(UVICORN_ERROR_LOGGER)
        original_propagate = server_logger.propagate
        server_logger.propagate = True
        try:
            OpenTelemetrySettings._attach_to_server_loggers(_handler())
            assert _otel_handlers(server_logger) == []
        finally:
            server_logger.propagate = original_propagate

    def test_repeated_configuration_does_not_stack_handlers(self):
        server_logger = logging.getLogger(UVICORN_ERROR_LOGGER)
        original_propagate = server_logger.propagate
        server_logger.propagate = False
        try:
            OpenTelemetrySettings._attach_to_server_loggers(_handler())
            OpenTelemetrySettings._attach_to_server_loggers(_handler())
            assert len(_otel_handlers(server_logger)) == 1
        finally:
            server_logger.handlers = [h for h in server_logger.handlers if not isinstance(h, LoggingHandler)]
            server_logger.propagate = original_propagate
