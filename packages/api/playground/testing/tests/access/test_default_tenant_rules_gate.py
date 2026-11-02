"""Covers who may read the derived tenant ceiling.

The response enumerates every model this instance serves, unfiltered by the caller's own tenant, so it
must not be reachable with the per-service admin permission its neighbours on ``AccessController`` use —
that one is held by every tenant admin. Pinned here because the sysadmin plane's own gate is tested while
the platform endpoint it proxies to was not, which is how the broader guard slipped through in the first
place.
"""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

from swiss_ai_hub.api.routes.access.access_capability_service import AccessCapabilityService
from swiss_ai_hub.api.routes.access.access_controller import AccessController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

ROUTE = "/api/v1/customer-tenant/access/default-tenant-rules"

# The instance serves three chat models; the tenant below is granted exactly one of them.
_ROSTER = {"text-generation": ["gemma-4-31B-it", "reserved-for-another-tenant"], "embedding": ["bge-m3"]}

_TENANT_CEILING = [
    "aihub.admin.agent.>",
    "aihub.admin.knowledge",
    "aihub.admin.knowledge.>",
    "aihub.admin.process.>",
    "aihub.admin.service.>",
    "aihub.user.memory.>",
    "aihub.user.model.text-generation.gemma-4-31B-it",
]


class _AuthHandler(AuthHandler):
    """A tenant admin holding the seeded ``AIHubAdmin`` role, sysadmin or not."""

    def __init__(self, *, is_sys_admin: bool) -> None:
        self._is_sys_admin = is_sys_admin

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        return UserIdentity(
            id="68b1df1f4fa54f9aeab2e6b7",
            name="Tenant Admin",
            email="tenant-admin@customer.example",
            roles=["AIHubAdmin"],
            acting_within_tenant=TenantIdentity(
                id="customer-tenant", name="Customer Tenant", access_rules=list(_TENANT_CEILING)
            ),
            is_sys_admin=self._is_sys_admin,
        )


@pytest.fixture(autouse=True)
def _stub_roster_and_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIHUB_TENANT_DEFAULT_ACCESS_EXCLUDED_MODELS", "")
    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", lambda roles, tenant_id: {"aihub.admin.>"})

    async def _roster() -> dict[str, list[str]]:
        return _ROSTER

    monkeypatch.setattr(AccessCapabilityService, "available_models_by_capability", _roster)


def _client(*, is_sys_admin: bool) -> TestClient:
    runner = ApiTestRunner()
    runner.mount(AccessController(auth=_AuthHandler(is_sys_admin=is_sys_admin)).get_default_tenant_rules())
    return TestClient(runner.create_app())


def test_a_tenant_admin_cannot_read_the_instance_wide_ceiling() -> None:
    """``aihub.admin.service.>`` is in every derived ceiling, so a tenant admin passes the per-service gate
    the neighbouring endpoints use — which is exactly why this one cannot rely on it."""
    response = _client(is_sys_admin=False).get(ROUTE)

    assert response.status_code == 403, response.text
    assert "reserved-for-another-tenant" not in response.text


def test_a_sysadmin_reads_the_derived_ceiling() -> None:
    response = _client(is_sys_admin=True).get(ROUTE)

    assert response.status_code == 200, response.text
    assert "aihub.user.model.text-generation.>" in response.json()
