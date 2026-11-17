"""Covers where a provisioned tenant's access ceiling comes from when the external syncer names none.

A new tenant must start from the same instance default as one configured by hand (never a broad wildcard,
which would expose other tenants' knowledge bases and agent profiles). An existing tenant keeps its own
ceiling, so the derivation is skipped and the omitted rules reach the service as "unchanged".
"""

from datetime import UTC, datetime

import pytest
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
    seen: list[list[str] | None] = []

    async def _provision(data) -> TenantResponse:  # noqa: ANN001
        seen.append(data.access_rules)
        now = datetime.now(UTC)
        return TenantResponse(
            id="lcdm-5",
            name=data.name,
            description=data.description,
            access_rules=data.access_rules or [],
            lcdm_tenant_id=data.lcdm_tenant_id,
            state=TenantState.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    monkeypatch.setattr(TenantAdminService, "provision_tenant", _provision)
    return seen


@pytest.fixture
def stub_proxy(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    async def _fetch(base_url: str, tenant_id: str, request) -> list[str]:  # noqa: ANN001
        calls.append(tenant_id)
        return list(DERIVED)

    monkeypatch.setattr(PlatformAccessProxy, "fetch_default_tenant_rules", _fetch)
    monkeypatch.setattr(PlatformAccessProxy, "base_url_or_raise", lambda runner: "http://api:8000")
    return calls


@pytest.fixture
def client() -> TestClient:
    runner = ApiTestRunner()
    runner.mount(TenantAdminController(auth=_SysAdminAuthHandler()).provision_tenant())
    return TestClient(runner.create_app())


_PAYLOAD = {"tenant_id": "lcdm-5", "name": "Palme", "lcdm_tenant_id": 5}


def test_new_tenant_without_rules_gets_the_derived_default(client, captured_rules, stub_proxy, monkeypatch) -> None:
    monkeypatch.setattr(TenantAdminService, "is_configured", lambda tenant_id: False)

    response = client.post(f"{BASE}/provision", json=_PAYLOAD)

    assert response.status_code == 200, response.text
    assert response.json()["lcdm_tenant_id"] == 5
    assert captured_rules == [DERIVED]
    assert "aihub.admin.>" not in captured_rules[0]


def test_existing_tenant_without_rules_keeps_its_ceiling(client, captured_rules, stub_proxy, monkeypatch) -> None:
    monkeypatch.setattr(TenantAdminService, "is_configured", lambda tenant_id: True)

    response = client.post(f"{BASE}/provision", json=_PAYLOAD)

    assert response.status_code == 200, response.text
    assert captured_rules == [None]
    assert stub_proxy == []


def test_explicit_rules_are_not_replaced_by_the_default(client, captured_rules, stub_proxy, monkeypatch) -> None:
    monkeypatch.setattr(TenantAdminService, "is_configured", lambda tenant_id: False)

    response = client.post(f"{BASE}/provision", json={**_PAYLOAD, "access_rules": []})

    assert response.status_code == 200, response.text
    assert captured_rules == [[]]
    assert stub_proxy == []
