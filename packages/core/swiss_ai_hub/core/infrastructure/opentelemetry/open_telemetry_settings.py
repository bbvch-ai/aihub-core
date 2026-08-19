import logging
from typing import Annotated, ClassVar, Literal

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter as GRPCLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HTTPLogExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanLimits, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings

logger = logging.getLogger(__name__)


class OpenTelemetrySettings(EnvironmentSettings):
    """OpenTelemetry configuration settings for any OTLP-compatible backend."""

    model_config = EnvironmentSettings.create_settings_config("OTEL_")

    # Loggers the ASGI server re-parents away from root: gunicorn's UvicornWorker gives them
    # its own handlers and sets propagate=False, so the root handler never sees "Exception in
    # ASGI application" — the only record carrying the traceback of an unhandled 500, and thus
    # the reason those 500s were invisible in the observability backend.
    SERVER_LOGGER_NAMES: ClassVar[tuple[str, ...]] = ("uvicorn", "uvicorn.error", "gunicorn.error")

    ENABLED: Annotated[bool, Field(description="Enable/disable OpenTelemetry tracing entirely")] = False
    RESOURCE_SERVICE_NAME: Annotated[str | None, Field(description="Resource service name")] = None
    RESOURCE_SERVICE_VERSION: Annotated[str | None, Field(description="Resource service version")] = None
    RESOURCE_SERVICE_NAMESPACE: Annotated[str | None, Field(description="Resource service namespace")] = None
    EXPORTER_OTLP_ENDPOINT: Annotated[str | None, Field(description="OTLP exporter endpoint URL")] = None
    EXPORTER_OTLP_PROTOCOL: Annotated[Literal["grpc", "http"], Field(description="OTLP protocol")] = "grpc"
    EXPORTER_OTLP_INSECURE: Annotated[bool, Field(description="Use insecure connection (no TLS) for gRPC")] = True

    def configure_tracing(self) -> TracerProvider | None:
        """Configure OpenTelemetry tracing for any OTLP-compatible backend."""
        if not self.ENABLED:
            logger.info("OpenTelemetry tracing disabled: OTEL_ENABLED=False")
            return None

        if not self.EXPORTER_OTLP_ENDPOINT:
            raise ValueError(
                "OpenTelemetry is enabled (OTEL_ENABLED=True) but OTEL_EXPORTER_OTLP_ENDPOINT is not configured. "
                "Either set OTEL_ENABLED=False to disable tracing or provide a valid OTLP endpoint."
            )

        if not all([self.RESOURCE_SERVICE_NAME, self.RESOURCE_SERVICE_VERSION, self.RESOURCE_SERVICE_NAMESPACE]):
            raise ValueError(
                "OpenTelemetry is enabled but missing required service configuration. "
                "Please set OTEL_RESOURCE_SERVICE_NAME, OTEL_RESOURCE_SERVICE_VERSION, "
                "and OTEL_RESOURCE_SERVICE_NAMESPACE."
            )

        resource = Resource.create(
            {
                "service.name": self.RESOURCE_SERVICE_NAME,
                "service.version": self.RESOURCE_SERVICE_VERSION,
                "service.namespace": self.RESOURCE_SERVICE_NAMESPACE,
            }
        )

        # RetrieverEvent spans can exceed the default 128-attribute limit
        span_limits = SpanLimits(max_attributes=512)
        tracer_provider = TracerProvider(resource=resource, span_limits=span_limits)

        if self.EXPORTER_OTLP_PROTOCOL == "grpc":
            otlp_exporter = GRPCSpanExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT, insecure=self.EXPORTER_OTLP_INSECURE)
        else:
            otlp_exporter = HTTPSpanExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT)

        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        trace.set_tracer_provider(tracer_provider)
        return tracer_provider

    def configure_logging(self) -> LoggerProvider | None:
        """Configure OpenTelemetry logging for any OTLP-compatible backend."""
        if not self.ENABLED:
            logger.info("OpenTelemetry logging disabled: OTEL_ENABLED=False")
            return None

        if not self.EXPORTER_OTLP_ENDPOINT:
            raise ValueError(
                "OpenTelemetry is enabled (OTEL_ENABLED=True) but OTEL_EXPORTER_OTLP_ENDPOINT is not configured. "
                "Either set OTEL_ENABLED=False to disable logging or provide a valid OTLP endpoint."
            )

        if not all([self.RESOURCE_SERVICE_NAME, self.RESOURCE_SERVICE_VERSION, self.RESOURCE_SERVICE_NAMESPACE]):
            raise ValueError(
                "OpenTelemetry is enabled but missing required service configuration. "
                "Please set OTEL_RESOURCE_SERVICE_NAME, OTEL_RESOURCE_SERVICE_VERSION, "
                "and OTEL_RESOURCE_SERVICE_NAMESPACE."
            )

        resource = Resource.create(
            {
                "service.name": self.RESOURCE_SERVICE_NAME,
                "service.version": self.RESOURCE_SERVICE_VERSION,
                "service.namespace": self.RESOURCE_SERVICE_NAMESPACE,
            }
        )

        logger_provider = LoggerProvider(resource=resource)

        if self.EXPORTER_OTLP_PROTOCOL == "grpc":
            otlp_log_exporter = GRPCLogExporter(
                endpoint=self.EXPORTER_OTLP_ENDPOINT, insecure=self.EXPORTER_OTLP_INSECURE
            )
        else:
            otlp_log_exporter = HTTPLogExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT)

        log_processor = BatchLogRecordProcessor(otlp_log_exporter)
        logger_provider.add_log_record_processor(log_processor)

        set_logger_provider(logger_provider)

        otel_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
        OpenTelemetrySettings._attach_handler(logging.getLogger(), otel_handler)
        OpenTelemetrySettings._attach_to_server_loggers(otel_handler)

        return logger_provider

    @staticmethod
    def _attach_to_server_loggers(handler: LoggingHandler) -> None:
        """Only the ones that stopped propagating: a server logger left on the default chain
        already reaches the root handler, and handling it twice would export every record twice."""
        for logger_name in OpenTelemetrySettings.SERVER_LOGGER_NAMES:
            server_logger = logging.getLogger(logger_name)
            if not server_logger.propagate:
                OpenTelemetrySettings._attach_handler(server_logger, handler)

    @staticmethod
    def _attach_handler(target: logging.Logger, handler: LoggingHandler) -> None:
        """Idempotent because configure_logging runs once per worker process and a stacked
        handler would export every record twice."""
        if not any(isinstance(existing, LoggingHandler) for existing in target.handlers):
            target.addHandler(handler)
