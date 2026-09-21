import logging
import threading
from typing import Any
from unittest.mock import patch

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider

from swiss_ai_hub.core.infrastructure.opentelemetry import open_telemetry_settings as settings_module
from swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings import OpenTelemetrySettings

pytestmark = pytest.mark.unit

OTLP_ENDPOINT = "http://localhost:4317"
OTLP_TIMEOUT = 60


def _enabled_settings(**overrides: Any) -> OpenTelemetrySettings:
    return OpenTelemetrySettings(
        **{
            "ENABLED": True,
            "METRICS_ENABLED": True,
            "EXPORTER_OTLP_ENDPOINT": OTLP_ENDPOINT,
            "RESOURCE_SERVICE_NAME": "api",
            "RESOURCE_SERVICE_VERSION": "0.0.1",
            "RESOURCE_SERVICE_NAMESPACE": "swiss-ai-hub",
            **overrides,
        }
    )


def _enabled_provider(**overrides: Any) -> MeterProvider:
    """
    Narrowing accessor for the tests that exercise the enabled path. configure_metrics() returns
    MeterProvider | None, so chaining onto it directly would dereference an Optional — and would
    surface a configuration regression as an AttributeError rather than as this assertion.
    """
    provider = _enabled_settings(**overrides).configure_metrics()

    assert provider is not None
    return provider


def _log_record(logger_name: str) -> logging.LogRecord:
    return logging.LogRecord(logger_name, logging.WARNING, __file__, 1, "msg", None, None)


def test_metrics_are_off_by_default() -> None:
    """Regression guard for issue #1496: request metrics must never be on unless asked for."""
    assert OpenTelemetrySettings.model_fields["METRICS_ENABLED"].default is False


def test_tracing_alone_does_not_enable_metrics() -> None:
    """OTEL_ENABLED turns on traces only — metrics need their own opt-in."""
    assert _enabled_settings(METRICS_ENABLED=False).configure_metrics() is None


def test_metrics_disabled_needs_no_otlp_endpoint() -> None:
    """The disabled path must stay inert, not raise on missing configuration."""
    settings = OpenTelemetrySettings(ENABLED=True, METRICS_ENABLED=False, EXPORTER_OTLP_ENDPOINT=None)

    assert settings.configure_metrics() is None


def test_both_flags_enabled_returns_a_real_meter_provider() -> None:
    provider = _enabled_settings().configure_metrics()

    assert isinstance(provider, MeterProvider)
    provider.shutdown()


def test_configure_metrics_does_not_set_the_global_meter_provider() -> None:
    """
    The provider must stay scoped to the caller that receives it. AihubInstrumentor
    instruments httpx/requests/aiohttp/botocore/asyncio without an explicit meter_provider,
    so a global one would also switch on client-side metrics nothing asked for — and the
    collector's filter/metrics_cardinality backstop only names http.server.*.

    Asserts on the call rather than on get_meter_provider(): OTel ignores every
    set_meter_provider() after the first, so an identity check silently passes.
    """
    with patch.object(metrics, "set_meter_provider") as set_global_provider:
        provider = _enabled_provider()

    set_global_provider.assert_not_called()
    provider.shutdown()


def test_metrics_enabled_without_endpoint_fails_loudly() -> None:
    settings = OpenTelemetrySettings(ENABLED=True, METRICS_ENABLED=True, EXPORTER_OTLP_ENDPOINT=None)

    with pytest.raises(ValueError, match="OTEL_EXPORTER_OTLP_ENDPOINT"):
        settings.configure_metrics()


def test_grpc_protocol_passes_the_insecure_flag() -> None:
    """
    The two exporter arms are asymmetric on purpose — only gRPC takes `insecure`, mirroring
    configure_tracing(). Pinning it keeps a later "tidy-up" from passing it to the HTTP exporter,
    which does not accept it.
    """
    with patch.object(settings_module, "GRPCMetricExporter") as grpc_exporter:
        _enabled_provider(EXPORTER_OTLP_PROTOCOL="grpc", EXPORTER_OTLP_INSECURE=True).shutdown()

    grpc_exporter.assert_called_once_with(endpoint=OTLP_ENDPOINT, insecure=True, timeout=OTLP_TIMEOUT)


def test_http_protocol_uses_the_http_exporter_without_insecure() -> None:
    """The HTTP arm was the branch left uncovered when metrics were introduced."""
    with patch.object(settings_module, "HTTPMetricExporter") as http_exporter:
        _enabled_provider(EXPORTER_OTLP_PROTOCOL="http").shutdown()

    http_exporter.assert_called_once_with(endpoint=OTLP_ENDPOINT, timeout=OTLP_TIMEOUT)


def test_the_export_timeout_default_covers_a_container_recreate() -> None:
    """
    Regression guard for the nightly.951 log loss. The SDK's 10s default is the entire retry
    budget, so any collector gap longer than ~7s drops the batch — and a container recreate is
    measured in tens of seconds (27.4s on that deploy). Lowering this back towards the default
    silently reintroduces the data loss, hence the pin.
    """
    assert OpenTelemetrySettings.model_fields["EXPORTER_OTLP_TIMEOUT"].default == OTLP_TIMEOUT


def test_the_retry_ladder_fits_inside_the_configured_timeout() -> None:
    """
    The timeout is a budget the backoff ladder spends, not a per-attempt limit: the exporter
    abandons the batch once the next backoff would overrun `deadline = start + timeout`. A budget
    that cuts the ladder short wastes the remaining attempts, so pin the relationship rather than
    just the number — the last of the six attempts starts at 1+2+4+8+16 = 31s.
    """
    ladder_end_seconds = sum(2**attempt for attempt in range(5))

    assert ladder_end_seconds < OpenTelemetrySettings.model_fields["EXPORTER_OTLP_TIMEOUT"].default


def test_the_otlp_handler_ignores_sdk_internal_records() -> None:
    """
    "Queue full, dropping logs." is emitted from inside BatchLogRecordProcessor on the calling
    thread, so routing it back through the root handler re-enters the export path. Exporter
    self-reports run on the export worker thread and must keep flowing — they are the only
    evidence in the backend that telemetry was lost.
    """
    is_exported = OpenTelemetrySettings._is_not_sdk_internal_record

    assert not is_exported(_log_record("opentelemetry.sdk._shared_internal"))
    assert not is_exported(_log_record("opentelemetry.sdk.trace"))
    assert is_exported(_log_record("opentelemetry.exporter.otlp.proto.grpc.exporter"))
    assert is_exported(_log_record("swiss_ai_hub.core.routes.health"))


@pytest.mark.parametrize(
    "missing_attribute",
    ["RESOURCE_SERVICE_NAME", "RESOURCE_SERVICE_VERSION", "RESOURCE_SERVICE_NAMESPACE"],
)
def test_every_service_attribute_is_required(missing_attribute: str) -> None:
    """
    All three attributes gate the resource, not just the first one. Worth pinning now that a
    single _build_resource() serves tracing, metrics and logging: a regression here would
    silently ship unidentifiable telemetry from all three at once.
    """
    settings = _enabled_settings(**{missing_attribute: None})

    with pytest.raises(ValueError, match="OTEL_RESOURCE_SERVICE_NAME"):
        settings.configure_metrics()


def test_the_resource_carries_all_three_service_attributes() -> None:
    """Guards the extraction itself: the shared resource must still describe the service."""
    resource = _enabled_settings()._build_resource()

    assert resource.attributes["service.name"] == "api"
    assert resource.attributes["service.version"] == "0.0.1"
    assert resource.attributes["service.namespace"] == "swiss-ai-hub"


def test_failed_validation_starts_no_exporter_thread() -> None:
    """
    Ordering guard. PeriodicExportingMetricReader starts a daemon thread in its constructor, so
    validating after building it orphans that thread: nothing owns it, nothing can shut it down,
    and it logs "Cannot call collect on a MetricReader until it is registered on a MeterProvider"
    on every tick for the life of the process. Everything the reader needs must therefore be
    validated before it is constructed.
    """
    settings = _enabled_settings(RESOURCE_SERVICE_NAMESPACE=None)
    threads_before = {id(thread) for thread in threading.enumerate()}

    with pytest.raises(ValueError, match="OTEL_RESOURCE_SERVICE_NAME"):
        settings.configure_metrics()

    leaked = [thread.name for thread in threading.enumerate() if id(thread) not in threads_before]
    assert leaked == []
