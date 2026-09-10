import logging
from typing import Annotated, ClassVar, Literal

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

    # Loggers the ASGI server re-parents away from root: gunicorn's UvicornWorker gives them
    # its own handlers and sets propagate=False, so the root handler never sees "Exception in
    # ASGI application" — the only record carrying the traceback of an unhandled 500, and thus
    # the reason those 500s were invisible in the observability backend.
    SERVER_LOGGER_NAMES: ClassVar[tuple[str, ...]] = ("uvicorn", "uvicorn.error", "gunicorn.error")

    ENABLED: Annotated[bool, Field(description="Enable/disable OpenTelemetry tracing entirely")] = False
    METRICS_ENABLED: Annotated[
        bool, Field(description="Enable/disable OpenTelemetry request metrics (separate from tracing)")
    ] = False
    # The SDK's 10s default is the whole retry budget, not a per-attempt timeout: the exporter sets
    # deadline = now + timeout once, then abandons the batch as soon as the next backoff
    # (1s, 2s, 4s, 8s...) would overrun it — three attempts, ~7s, then "Failed to export ... error
    # code: StatusCode.UNAVAILABLE" and the records are gone. A collector restart takes longer than
    # that: on nightly.951 sysadmin-api came up 27.4s before the recreated collector and lost its
    # startup log.
    #
    # 60s does NOT buy 60s of coverage: the hardcoded _MAX_RETRYS=6 ladder makes its last attempt
    # at ~31s, so that is the real ceiling, and against the 27.4s measured on that deploy the
    # margin is only ~4s. The depends_on chain in docker-compose is what actually removes the
    # ordering gap — this value only has to survive an unplanned collector restart. Raising it
    # further trades queue headroom for a backend that is slow rather than absent: the queue keeps
    # filling while the export thread waits, and BatchLogRecordProcessor.shutdown() only joins the
    # worker for 30s, so anything past that is unreachable on the shutdown path anyway.
    #
    # NOTE: with the OTEL_ prefix this field's variable is OTEL_EXPORTER_OTLP_TIMEOUT, the name the
    # OTel spec reserves — and the spec measures it in MILLISECONDS. Python's SDK deviates and
    # reads seconds, so the two agree here, but a value placed in shared deployment config would be
    # read as 60ms by any non-Python OTLP client in the stack.
    EXPORTER_OTLP_TIMEOUT: Annotated[int, Field(description="Seconds an OTLP export may spend retrying")] = 60
    BLRP_MAX_QUEUE_SIZE: Annotated[int, Field(description="Log records buffered before new ones are dropped")] = 16384
    BLRP_MAX_EXPORT_BATCH_SIZE: Annotated[int, Field(description="Log records per OTLP export")] = 2048
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
            otlp_exporter = GRPCSpanExporter(
                endpoint=self.EXPORTER_OTLP_ENDPOINT,
                insecure=self.EXPORTER_OTLP_INSECURE,
                timeout=self.EXPORTER_OTLP_TIMEOUT,
            )
        else:
            otlp_exporter = HTTPSpanExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT, timeout=self.EXPORTER_OTLP_TIMEOUT)

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

        # Built before the exporter, not inline in the MeterProvider call: constructing a
        # PeriodicExportingMetricReader already starts a daemon thread, so a validation error
        # raised after it would orphan that thread — it would then log "Cannot call collect on a
        # MetricReader until it is registered on a MeterProvider" on every tick for the life of
        # the process.
        resource = self._build_resource()

        if self.EXPORTER_OTLP_PROTOCOL == "grpc":
            otlp_exporter = GRPCMetricExporter(
                endpoint=self.EXPORTER_OTLP_ENDPOINT,
                insecure=self.EXPORTER_OTLP_INSECURE,
                timeout=self.EXPORTER_OTLP_TIMEOUT,
            )
        else:
            otlp_exporter = HTTPMetricExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT, timeout=self.EXPORTER_OTLP_TIMEOUT)

        metric_reader = PeriodicExportingMetricReader(otlp_exporter)
        return MeterProvider(resource=resource, metric_readers=[metric_reader])

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
                endpoint=self.EXPORTER_OTLP_ENDPOINT,
                insecure=self.EXPORTER_OTLP_INSECURE,
                timeout=self.EXPORTER_OTLP_TIMEOUT,
            )
        else:
            otlp_log_exporter = HTTPLogExporter(
                endpoint=self.EXPORTER_OTLP_ENDPOINT, timeout=self.EXPORTER_OTLP_TIMEOUT
            )

        # The SDK defaults (2048 queued, 512 per export) silently discard records once the queue is
        # full, and nothing logs the discard — so a burst looks like a complete log in the backend
        # while records are missing from it. Measured against a real collector on a 5000-record
        # burst, counting the records that arrived: the defaults delivered 2986, these values
        # delivered 5000. The batch
        # size matters as much as the queue, since it is what lets the export worker drain faster
        # than a burst fills it. Field names match the OTel spec's OTEL_BLRP_* variables, so an
        # operator can still tune a single service without a code change.
        log_processor = BatchLogRecordProcessor(
            otlp_log_exporter,
            max_queue_size=self.BLRP_MAX_QUEUE_SIZE,
            max_export_batch_size=self.BLRP_MAX_EXPORT_BATCH_SIZE,
        )
        logger_provider.add_log_record_processor(log_processor)

        set_logger_provider(logger_provider)

        otel_handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
        otel_handler.addFilter(OpenTelemetrySettings._is_not_sdk_internal_record)
        OpenTelemetrySettings._attach_handler(logging.getLogger(), otel_handler)
        OpenTelemetrySettings._attach_to_server_loggers(otel_handler)

        return logger_provider

    @staticmethod
    def _is_not_sdk_internal_record(record: logging.LogRecord) -> bool:
        """
        Keeps the OTLP handler off its own SDK's diagnostics, so reporting a problem with log
        export cannot itself go through log export.

        The case that motivates it: BatchLogRecordProcessor reports a full queue with
        `_logger.warning("Queue full, dropping %s.")` on the *calling* thread, so with the handler
        on the root logger that warning re-enters on_emit(). The SDK already breaks the loop —
        _shared_internal attaches its own DuplicateFilter for exactly this ("prevent endlessly
        logging the same log in cases where logging itself is failing"), which caps the nesting at
        depth 2 — but that is an internal of a floating `>=1.39.1` pin, and re-entering the export
        path to report that the export path is full is pointless work regardless.

        Scope is the whole `opentelemetry.sdk.` tree, not just the queue warning, because the
        emitting module has already moved once (_logs._internal.export -> _shared_internal) and a
        prefix survives that. The cost is that SDK-side diagnostics (ended-span writes, instrument
        name conflicts, resource detector errors) no longer reach the backend; they still reach
        whatever console handlers sit on the root logger.

        Exporter self-reports ("Failed to export logs to ...") are deliberately NOT filtered: they
        are emitted on the export worker thread, cannot re-enter, and are the only signal in the
        backend that telemetry was lost.
        """
        return not record.name.startswith("opentelemetry.sdk.")

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
