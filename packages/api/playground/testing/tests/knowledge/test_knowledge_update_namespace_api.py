"""Covers who may rename a knowledge folder through the HTTP route.

Creating a folder grants its creator a role holding only ``aihub.admin.knowledge.<database>.<folder>``. The
route guard must accept exactly that rule for that folder — and nothing broader — which it could not while the
path carried ObjectIds (aihub-core-private#290). Asserted over HTTP so the guard and the controller's
forwarding are exercised together.
"""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

from swiss_ai_hub.api.routes.knowledge.dto.namespace_response import NamespaceResponse
from swiss_ai_hub.api.routes.knowledge.dto.update_namespace_request import UpdateNamespaceRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_controller import KnowledgeController
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

DATABASE = "research"
NAMESPACE = "reports"
SIBLING_NAMESPACE = "contracts"

# What ``KnowledgeService.create_namespace`` grants through the auto-created ``KnowledgeResearchReportsAdmin``.
_FOLDER_ADMIN_RULES = {
    "aihub.user.service.knowledge",
    f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}",
    f"aihub.admin.knowledge.{DATABASE}.{NAMESPACE}",
}


class _AuthHandler(AuthHandler):
    """A tenant member whose only knowledge grant is the per-folder admin role."""

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        return UserIdentity(
            id="68b1df1f4fa54f9aeab2e6b7",
            name="Folder Admin",
            email="folder-admin@customer.example",
            roles=["KnowledgeResearchReportsAdmin"],
            acting_within_tenant=TenantIdentity(
                id="customer-tenant", name="Customer Tenant", access_rules=["aihub.user.>", "aihub.admin.>"]
            ),
        )


@pytest.fixture
def forwarded(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Records what the controller hands the service, so the guard is the only thing under test."""
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", lambda roles, tenant_id: set(_FOLDER_ADMIN_RULES))

    async def _update_namespace(
        database: str, namespace: str, request: UpdateNamespaceRequest, t, user, llm_config=None
    ) -> NamespaceResponse:
        calls.append((database, namespace))
        return NamespaceResponse(
            id="6ab376716f0bf3e684dd5cc0",
            bucket_id="6ab3763616f0bf3e684dd5b7",
            namespace_name=namespace,
            folder_name=namespace,
            display_name=request.display_name,
            description=request.description,
        )

    monkeypatch.setattr(KnowledgeService, "update_namespace", _update_namespace)
    return calls


def _rename(namespace: str):
    runner = ApiTestRunner()
    runner.mount(KnowledgeController(auth=_AuthHandler()).update_namespace())
    return TestClient(runner.create_app()).put(
        f"/api/v1/customer-tenant/knowledge/databases/{DATABASE}/namespaces/{namespace}",
        json={"display_name": "Quarterly reports", "description": "Finance only"},
    )


def test_a_folder_admin_can_rename_their_folder(forwarded: list[tuple[str, str]]) -> None:
    response = _rename(NAMESPACE)

    assert response.status_code == 200, response.text
    assert forwarded == [(DATABASE, NAMESPACE)]


def test_a_folder_admin_cannot_rename_a_sibling_folder(forwarded: list[tuple[str, str]]) -> None:
    response = _rename(SIBLING_NAMESPACE)

    assert response.status_code == 403, response.text
    assert forwarded == []
