from typing import Any
from unittest.mock import patch

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from prometheus_client import CollectorRegistry, generate_latest

from swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings import OpenTelemetrySettings

pytestmark = pytest.mark.unit


def _enabled_settings(**overrides: Any) -> OpenTelemetrySettings:
    return OpenTelemetrySettings(
        **{
            "ENABLED": True,
            "METRICS_ENABLED": True,
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
    assert _enabled_settings(METRICS_ENABLED=False).configure_metrics(CollectorRegistry()) is None


def test_disabled_path_stays_inert_without_a_registry() -> None:
    """The disabled path must not raise just because the caller passed nothing."""
    assert OpenTelemetrySettings(ENABLED=True, METRICS_ENABLED=False).configure_metrics() is None


def test_enabled_returns_a_real_meter_provider() -> None:
    assert isinstance(_enabled_settings().configure_metrics(CollectorRegistry()), MeterProvider)


def test_scraping_needs_no_otlp_endpoint() -> None:
    """
    The point of scraping: the store pulls, so no exporter endpoint is involved. Requiring one
    would make the scrape path inherit a configuration burden it has no use for.
    """
    settings = _enabled_settings(EXPORTER_OTLP_ENDPOINT=None)

    assert isinstance(settings.configure_metrics(CollectorRegistry()), MeterProvider)


def test_enabled_without_registry_fails_loudly() -> None:
    """
    Falling back to prometheus_client's global REGISTRY would work once and then break, so a
    missing registry has to be an error rather than a silent default.
    """
    with pytest.raises(ValueError, match="CollectorRegistry"):
        _enabled_settings().configure_metrics()


def test_each_registry_is_independent() -> None:
    """
    Pins the failure the global default registry produces: registering the same collector twice
    raises "Duplicated timeseries". The API builds one app per test, so this has to hold for
    arbitrarily many providers in one process.
    """
    first = _enabled_settings().configure_metrics(CollectorRegistry())
    second = _enabled_settings().configure_metrics(CollectorRegistry())

    assert first is not second


def test_recorded_measurements_reach_the_scrape_output() -> None:
    """
    End-to-end within the process: a measurement recorded through the provider must be readable
    in the registry's exposition text. This is what the OTLP push path could not demonstrate —
    there, every http.server.* metric is named in the collector's filter/metrics_cardinality.
    """
    registry = CollectorRegistry()
    provider = _enabled_settings().configure_metrics(registry)

    provider.get_meter("test").create_counter("requests").add(1, {"route": "/health"})

    exposition = generate_latest(registry).decode()
    assert "requests_total" in exposition
    assert 'route="/health"' in exposition


def test_configure_metrics_does_not_set_the_global_meter_provider() -> None:
    """
    The provider must stay scoped to the caller that receives it. AihubInstrumentor instruments
    httpx/requests/aiohttp/botocore/asyncio without an explicit meter_provider, so a global one
    would also switch on client-side metrics nothing asked for.

    Asserts on the call rather than on get_meter_provider(): OTel ignores every
    set_meter_provider() after the first, so an identity check silently passes.
    """
    with patch.object(metrics, "set_meter_provider") as set_global_provider:
        assert _enabled_settings().configure_metrics(CollectorRegistry()) is not None

    set_global_provider.assert_not_called()


def test_metrics_still_require_service_attributes() -> None:
    """The scrape path drops the endpoint requirement, not the resource identity one."""
    settings = _enabled_settings(RESOURCE_SERVICE_NAMESPACE=None)

    with pytest.raises(ValueError, match="OTEL_RESOURCE_SERVICE_NAMESPACE"):
        settings.configure_metrics(CollectorRegistry())
