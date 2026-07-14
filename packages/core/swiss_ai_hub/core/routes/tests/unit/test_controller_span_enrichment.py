from types import SimpleNamespace

import pytest

from swiss_ai_hub.core.routes import controller as controller_module
from swiss_ai_hub.core.routes.controller import Controller
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user


class _RecordingSpan:
    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def is_recording(self) -> bool:
        return True

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes[key] = value


def _make_request(path: str) -> SimpleNamespace:
    return SimpleNamespace(
        path_params={"tenant_id": "active", "agent_class": "DemoAgent", "agent_id": "abc123"},
        url=SimpleNamespace(path=path),
        client=SimpleNamespace(host="10.0.0.1"),
    )


def test_enrich_span_keeps_http_route_as_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression guard for issue #1496: never overwrite http.route with the concrete URL.

    De-templating http.route exploded metric/label cardinality; the concrete path must land
    on url.path instead so the bounded route template survives.
    """
    span = _RecordingSpan()
    monkeypatch.setattr(controller_module.trace, "get_current_span", lambda: span)

    path = "/api/v1/active/agents/DemoAgent/abc123"
    Controller._enrich_span_with_context(
        SimpleNamespace(service_name="demo"), fake_user(), _make_request(path), "aihub.user.agent"
    )

    assert "http.route" not in span.attributes
    assert span.attributes["url.path"] == path
