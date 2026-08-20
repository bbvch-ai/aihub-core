from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter
from starlette.applications import Starlette
from starlette.testclient import TestClient

from swiss_ai_hub.api.runners.api_runner import CAPTURED_REQUEST_HEADERS, ApiRunner


def test_captured_request_headers_is_a_bounded_allowlist() -> None:
    """Regression guard for issue #1496: header capture must not be the catch-all [".*"].

    Capturing every header re-inflated trace/metric cardinality; the allowlist must stay
    small and explicit.
    """
    assert CAPTURED_REQUEST_HEADERS != [".*"]
    assert ".*" not in CAPTURED_REQUEST_HEADERS
    assert 0 < len(CAPTURED_REQUEST_HEADERS) <= 5
    assert all(isinstance(header, str) for header in CAPTURED_REQUEST_HEADERS)


def test_metrics_route_is_served_outside_the_api_path() -> None:
    """
    The scrape endpoint must sit on the outer Starlette app, not under api_path.

    Traefik routes this service on PathPrefix(`/api/v1`) only, so a route at /metrics is
    reachable from inside the network and not from the internet. Moving it under api_path would
    publish request latencies and the full route list, and would also turn it into an MCP
    resource via FastMCP.from_fastapi().
    """
    route = ApiRunner._build_metrics_route(CollectorRegistry())

    assert route.path == "/metrics"
    assert not route.path.startswith("/api")


def test_metrics_route_serves_the_registry_it_was_given() -> None:
    """A scraper must get this app's measurements in Prometheus exposition format."""
    registry = CollectorRegistry()
    Counter("aihub_probe", "probe counter", registry=registry).inc()

    app = Starlette(routes=[ApiRunner._build_metrics_route(registry)])
    response = TestClient(app).get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"] == CONTENT_TYPE_LATEST
    assert "aihub_probe_total" in response.text


def test_metrics_routes_from_separate_registries_do_not_share_series() -> None:
    """
    Two apps in one process must not see each other's metrics. This is the property that a
    per-app CollectorRegistry buys and prometheus_client's global REGISTRY would lose.
    """
    first_registry, second_registry = CollectorRegistry(), CollectorRegistry()
    Counter("aihub_first", "first", registry=first_registry).inc()
    Counter("aihub_second", "second", registry=second_registry).inc()

    first = TestClient(Starlette(routes=[ApiRunner._build_metrics_route(first_registry)])).get("/metrics")
    second = TestClient(Starlette(routes=[ApiRunner._build_metrics_route(second_registry)])).get("/metrics")

    assert "aihub_first_total" in first.text
    assert "aihub_second_total" not in first.text
    assert "aihub_second_total" in second.text
    assert "aihub_first_total" not in second.text
