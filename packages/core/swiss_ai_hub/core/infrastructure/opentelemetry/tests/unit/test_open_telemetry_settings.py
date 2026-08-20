from unittest.mock import patch

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider

from swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings import OpenTelemetrySettings

pytestmark = pytest.mark.unit


def _enabled_settings(**overrides) -> OpenTelemetrySettings:
    return OpenTelemetrySettings(
        **{
            "ENABLED": True,
            "METRICS_ENABLED": True,
            "EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
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
