"""The database listing carries classification state through the controller's access filtering (#2484).

The controller rebuilds every database it returns, so a field the service fills is lost unless it is passed on there
too. Only someone who may request classification is offered it.
"""

from datetime import UTC, datetime

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

from swiss_ai_hub.api.routes.knowledge.dto.database_dto import DatabaseDTO
from swiss_ai_hub.api.routes.knowledge.knowledge_controller import KnowledgeController
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

DATABASE = "invoices"
REQUESTED_AT = datetime(2026, 11, 17, 9, 30, tzinfo=UTC)
_READER_RULES = {"aihub.user.service.knowledge", f"aihub.user.knowledge.{DATABASE}.>"}
_ADMIN_RULES = _READER_RULES | {f"aihub.admin.knowledge.{DATABASE}"}


class _AuthHandler(AuthHandler):
    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        return UserIdentity(
            id="68b1df1f4fa54f9aeab2e6b7",
            name="Knowledge User",
            email="knowledge-user@customer.example",
            roles=["KnowledgeUser"],
            acting_within_tenant=TenantIdentity(
                id="customer-tenant", name="Customer Tenant", access_rules=["aihub.user.>", "aihub.admin.>"]
            ),
        )


def _listed_database(monkeypatch: pytest.MonkeyPatch, rules: set[str]) -> dict:
    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", lambda roles, tenant_id: set(rules))
    monkeypatch.setattr(
        KnowledgeService,
        "get_databases",
        lambda t: [
            DatabaseDTO(
                name=DATABASE,
                display_name="Invoices",
                source=None,
                deletable=True,
                ingestor="document_ingestion",
                classification_available=True,
                classification_requested_at=REQUESTED_AT,
                namespaces=[],
            )
        ],
    )
    runner = ApiTestRunner()
    runner.mount(KnowledgeController(auth=_AuthHandler()).get_databases())
    response = TestClient(runner.create_app()).get("/api/v1/customer-tenant/knowledge/databases")
    assert response.status_code == 200, response.text
    [database] = response.json()
    return database


def test_a_database_admin_is_offered_classification_and_sees_a_pending_request(monkeypatch: pytest.MonkeyPatch):
    database = _listed_database(monkeypatch, _ADMIN_RULES)

    assert database["classification_available"] is True
    assert datetime.fromisoformat(database["classification_requested_at"]) == REQUESTED_AT


def test_a_reader_is_not_offered_classification(monkeypatch: pytest.MonkeyPatch):
    database = _listed_database(monkeypatch, _READER_RULES)

    assert database["classification_available"] is False
    assert datetime.fromisoformat(database["classification_requested_at"]) == REQUESTED_AT
