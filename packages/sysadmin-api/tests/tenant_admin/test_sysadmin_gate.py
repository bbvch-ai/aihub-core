"""Verifies the ``sys_admin_user()`` gate on ``TenantAdminController`` denies non-sysadmins
end-to-end, not just at the auth dependency layer.

``TestAuthHandler`` builds an identity with ``is_sys_admin=False`` by default, so mounting
the controller behind it is enough to exercise the rejection path. Every endpoint shares
the same dependency, so one endpoint is representative; we hit all five anyway because the
registration is a fluent chain and any of them could silently lose the security decorator
during refactors.
"""

import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.api import ApiTestRunner
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_controller import TenantAdminController

BASE = "/api/v1/admin/tenants"


@pytest.fixture
def non_sysadmin_client():
    auth = TestAuthHandler()  # is_sys_admin defaults to False
    runner = ApiTestRunner()
    runner.mount(
        TenantAdminController(auth=auth)
        .list_tenants()
        .list_unconfigured_tenants()
        .get_tenant()
        .create_tenant_metadata()
        .update_tenant_metadata()
        .delete_tenant_metadata()
    )
    return TestClient(runner.create_app())


@pytest.mark.parametrize(
    "method, path, payload",
    [
        ("get", f"{BASE}/", None),
        ("get", f"{BASE}/unconfigured", None),
        ("get", f"{BASE}/some-tenant-id", None),
        ("post", f"{BASE}/", {"tenant_id": "x", "name": "X"}),
        ("patch", f"{BASE}/some-tenant-id", {"name": "X"}),
        ("delete", f"{BASE}/some-tenant-id", None),
    ],
)
def test_non_sysadmin_is_forbidden_from_every_endpoint(non_sysadmin_client, method, path, payload):
    response = (
        getattr(non_sysadmin_client, method)(path, json=payload)
        if payload
        else getattr(non_sysadmin_client, method)(path)
    )
    assert response.status_code == 403, (
        f"{method.upper()} {path}: expected 403 for non-sysadmin, got {response.status_code}: {response.text}"
    )
    assert "AIHubSysAdmin" in response.json().get("detail", ""), (
        f"403 detail should mention the required role; got {response.json()}"
    )
