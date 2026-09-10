"""Covers where a new tenant's access ceiling comes from when the request does not name one.

Omitting ``access_rules`` means "this instance's standard set", which only the platform API can answer —
the sysadmin plane has no model-gateway connection and deliberately does not gain one. An explicit empty
list is a different intent (a tenant that starts with nothing) and must survive untouched, which is why
the field is nullable rather than defaulting to ``[]``.
"""

from datetime import UTC, datetime

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from swiss_ai_hub.api import ApiTestRunner
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.sysadmin_api.routes.access.platform_access_proxy import PlatformAccessProxy
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.tenant_response import TenantResponse
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.dto.tenant_state import TenantState
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_controller import TenantAdminController
from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_service import TenantAdminService

BASE = "/api/v1/admin/tenants"
DERIVED = ["aihub.admin.agent.>", "aihub.user.model.text-generation.Kimi-K2_6"]


class _SysAdminAuthHandler(TestAuthHandler):
    async def authenticate_token(self, token_str: str, request=None):  # noqa: ANN001, ANN201
        return fake_user(is_sys_admin=True)


@pytest.fixture
def captured_rules(monkeypatch: pytest.MonkeyPatch) -> list[list[str] | None]:
    """Records what actually reached the service, which is the thing under test."""
    seen: list[list[str] | None] = []

    async def _create(data) -> TenantResponse:  # noqa: ANN001
        seen.append(data.access_rules)
        now = datetime.now(UTC)
        return TenantResponse(
            id="my-tenant",
            name=data.name,
            description=data.description,
            access_rules=data.access_rules or [],
            state=TenantState.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    monkeypatch.setattr(TenantAdminService, "create_tenant_metadata", _create)
    return seen


@pytest.fixture
def client() -> TestClient:
    runner = ApiTestRunner()
    runner.mount(TenantAdminController(auth=_SysAdminAuthHandler()).get_default_access_rules().create_tenant_metadata())
    return TestClient(runner.create_app())


@pytest.fixture
def stub_proxy(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    async def _fetch(base_url: str, tenant_id: str, request) -> list[str]:  # noqa: ANN001
        calls.append(tenant_id)
        return list(DERIVED)

    monkeypatch.setattr(PlatformAccessProxy, "fetch_default_tenant_rules", _fetch)
    monkeypatch.setattr(PlatformAccessProxy, "base_url_or_raise", lambda runner: "http://api:8000")
    return calls


def test_omitted_rules_fall_back_to_the_derived_default(client, captured_rules, stub_proxy) -> None:
    response = client.post(f"{BASE}/", json={"tenant_id": "my-tenant", "name": "My Tenant"})

    assert response.status_code == 201, response.text
    assert captured_rules == [DERIVED]


def test_the_default_is_resolved_against_the_acting_tenant(client, captured_rules, stub_proxy) -> None:
    """``active`` keeps this working without a concrete tenant id — none exists yet at create time."""
    client.post(f"{BASE}/", json={"tenant_id": "my-tenant", "name": "My Tenant"})

    assert stub_proxy == ["active"]


def test_explicit_empty_list_creates_a_tenant_with_no_access(client, captured_rules, stub_proxy) -> None:
    response = client.post(f"{BASE}/", json={"tenant_id": "my-tenant", "name": "My Tenant", "access_rules": []})

    assert response.status_code == 201, response.text
    assert captured_rules == [[]]
    assert stub_proxy == [], "an explicit choice must not be second-guessed by the derivation"


def test_explicit_rules_pass_through_untouched(client, captured_rules, stub_proxy) -> None:
    rules = ["aihub.admin.>"]

    response = client.post(f"{BASE}/", json={"tenant_id": "my-tenant", "name": "My Tenant", "access_rules": rules})

    assert response.status_code == 201, response.text
    assert captured_rules == [rules]
    assert stub_proxy == []


def test_unreachable_platform_api_creates_no_tenant(client, captured_rules, monkeypatch) -> None:
    """The derivation runs before every side effect, so a failure leaves the tenant Unconfigured and
    retryable rather than half-built."""

    async def _boom(base_url: str, tenant_id: str, request) -> list[str]:  # noqa: ANN001
        raise PlatformAccessProxy._gateway_error(httpx.ConnectError("connection refused"))

    monkeypatch.setattr(PlatformAccessProxy, "fetch_default_tenant_rules", _boom)
    monkeypatch.setattr(PlatformAccessProxy, "base_url_or_raise", lambda runner: "http://api:8000")

    response = client.post(f"{BASE}/", json={"tenant_id": "my-tenant", "name": "My Tenant"})

    assert response.status_code == 502, response.text
    assert captured_rules == [], "no tenant may be persisted when the ceiling could not be determined"


def test_default_access_rules_endpoint_returns_the_derived_ceiling(client, stub_proxy) -> None:
    response = client.get(f"{BASE}/default-access-rules")

    assert response.status_code == 200, response.text
    assert response.json() == DERIVED


def test_missing_platform_api_base_url_is_reported(client, captured_rules, monkeypatch) -> None:
    monkeypatch.setattr(
        PlatformAccessProxy,
        "base_url_or_raise",
        lambda runner: (_ for _ in ()).throw(HTTPException(status_code=500, detail="not configured")),
    )

    response = client.post(f"{BASE}/", json={"tenant_id": "my-tenant", "name": "My Tenant"})

    assert response.status_code == 500
    assert captured_rules == []
