from typing import Any
from unittest.mock import patch

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider

from swiss_ai_hub.core.infrastructure.opentelemetry import open_telemetry_settings as settings_module
from swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings import OpenTelemetrySettings

pytestmark = pytest.mark.unit

OTLP_ENDPOINT = "http://localhost:4317"


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
    assert isinstance(_enabled_settings().configure_metrics(), MeterProvider)


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
        assert _enabled_settings().configure_metrics() is not None

    set_global_provider.assert_not_called()


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
        _enabled_settings(EXPORTER_OTLP_PROTOCOL="grpc", EXPORTER_OTLP_INSECURE=True).configure_metrics()

    grpc_exporter.assert_called_once_with(endpoint=OTLP_ENDPOINT, insecure=True)


def test_http_protocol_uses_the_http_exporter_without_insecure() -> None:
    """The HTTP arm was the branch left uncovered when metrics were introduced."""
    with patch.object(settings_module, "HTTPMetricExporter") as http_exporter:
        _enabled_settings(EXPORTER_OTLP_PROTOCOL="http").configure_metrics()

    http_exporter.assert_called_once_with(endpoint=OTLP_ENDPOINT)


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
