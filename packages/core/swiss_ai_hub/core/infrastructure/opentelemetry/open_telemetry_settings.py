import logging
from typing import Annotated, Literal

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter as GRPCLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GRPCMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HTTPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HTTPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanLimits, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings

logger = logging.getLogger(__name__)


class OpenTelemetrySettings(EnvironmentSettings):
    """OpenTelemetry configuration settings for any OTLP-compatible backend."""

    model_config = EnvironmentSettings.create_settings_config("OTEL_")

    ENABLED: Annotated[bool, Field(description="Enable/disable OpenTelemetry tracing entirely")] = False
    METRICS_ENABLED: Annotated[
        bool, Field(description="Enable/disable OpenTelemetry request metrics (separate from tracing)")
    ] = False
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

        # RetrieverEvent spans can exceed the default 128-attribute limit
        span_limits = SpanLimits(max_attributes=512)
        tracer_provider = TracerProvider(resource=self._build_resource(), span_limits=span_limits)

        if self.EXPORTER_OTLP_PROTOCOL == "grpc":
            otlp_exporter = GRPCSpanExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT, insecure=self.EXPORTER_OTLP_INSECURE)
        else:
            otlp_exporter = HTTPSpanExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT)

        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        trace.set_tracer_provider(tracer_provider)
        return tracer_provider

    def configure_metrics(self) -> MeterProvider | None:
        """
        Configure OpenTelemetry request metrics for any OTLP-compatible backend.

        Separate from tracing: OTEL_ENABLED alone keeps this off, since the FastAPI/ASGI
        auto-instrumentation's request-count/duration histograms were the unbounded,
        high-cardinality metric source behind issue #1496. Requires both OTEL_ENABLED and
        OTEL_METRICS_ENABLED.

        Deliberately does NOT call metrics.set_meter_provider(): the httpx/requests/aiohttp/
        botocore/asyncio instrumentors in AihubInstrumentor take no explicit meter_provider, so
        setting the global one would also start emitting client-side metrics (http.client.duration
        and friends) that nothing asked for — and the collector's filter/metrics_cardinality
        backstop only names http.server.*, so those would reach a paid backend unfiltered. The
        caller passes the returned provider to the one instrumentor that should use it.
        """
        if not self.ENABLED or not self.METRICS_ENABLED:
            logger.info("OpenTelemetry metrics disabled: OTEL_ENABLED=False or OTEL_METRICS_ENABLED=False")
            return None

        if not self.EXPORTER_OTLP_ENDPOINT:
            raise ValueError(
                "OpenTelemetry metrics are enabled (OTEL_METRICS_ENABLED=True) but "
                "OTEL_EXPORTER_OTLP_ENDPOINT is not configured. Either set OTEL_METRICS_ENABLED=False "
                "to disable metrics or provide a valid OTLP endpoint."
            )

        if self.EXPORTER_OTLP_PROTOCOL == "grpc":
            otlp_exporter = GRPCMetricExporter(
                endpoint=self.EXPORTER_OTLP_ENDPOINT, insecure=self.EXPORTER_OTLP_INSECURE
            )
        else:
            otlp_exporter = HTTPMetricExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT)

        metric_reader = PeriodicExportingMetricReader(otlp_exporter)
        return MeterProvider(resource=self._build_resource(), metric_readers=[metric_reader])

    def _build_resource(self) -> Resource:
        """The three service attributes every backend keys on; shared by all configure_* methods."""
        if not all([self.RESOURCE_SERVICE_NAME, self.RESOURCE_SERVICE_VERSION, self.RESOURCE_SERVICE_NAMESPACE]):
            raise ValueError(
                "OpenTelemetry is enabled but missing required service configuration. "
                "Please set OTEL_RESOURCE_SERVICE_NAME, OTEL_RESOURCE_SERVICE_VERSION, "
                "and OTEL_RESOURCE_SERVICE_NAMESPACE."
            )

        return Resource.create(
            {
                "service.name": self.RESOURCE_SERVICE_NAME,
                "service.version": self.RESOURCE_SERVICE_VERSION,
                "service.namespace": self.RESOURCE_SERVICE_NAMESPACE,
            }
        )

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

        logger_provider = LoggerProvider(resource=self._build_resource())

        if self.EXPORTER_OTLP_PROTOCOL == "grpc":
            otlp_log_exporter = GRPCLogExporter(
                endpoint=self.EXPORTER_OTLP_ENDPOINT, insecure=self.EXPORTER_OTLP_INSECURE
            )
        else:
            otlp_log_exporter = HTTPLogExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT)

        log_processor = BatchLogRecordProcessor(otlp_log_exporter)
        logger_provider.add_log_record_processor(log_processor)

        set_logger_provider(logger_provider)

        root_logger = logging.getLogger()
        has_otel_handler = any(isinstance(h, LoggingHandler) for h in root_logger.handlers)
        if not has_otel_handler:
            otel_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
            root_logger.addHandler(otel_handler)

        return logger_provider
