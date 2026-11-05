"""Guards the re-mounted ``packages/api`` routes that sysadmin-web's inherited composables call same-origin.

A missing mount fails silently in the browser: the composable gets an error the web client only logs,
and the page renders empty.
"""

import pytest
from starlette.routing import Mount

from swiss_ai_hub.sysadmin_api.main import app


def _api_paths() -> dict[str, dict]:
    api = next(route.app for route in app.routes if isinstance(route, Mount) and route.path == "/api/v1")
    return api.openapi()["paths"]


@pytest.mark.parametrize(
    "path",
    [
        "/{tenant_id}/my-account/identity",
        "/my-tenants",
        "/{tenant_id}/users/",
        "/{tenant_id}/roles/",
    ],
)
def test_sysadmin_app_serves_get_route_used_by_sysadmin_web(path: str) -> None:
    assert "get" in _api_paths().get(path, {}), f"GET /api/v1{path} is not mounted on sysadmin-api"
