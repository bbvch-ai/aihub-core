"""Authorization tests for the two LLM-spend endpoints.

The entity-level tests exercise the aggregation; these exercise the authorization decision around it,
which is the security-critical half. Spend reveals who used which agents and how much, so a tenant
admin seeing another tenant's users is a cross-tenant data leak — and a regression there is silent,
since the query itself keeps working.
"""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from bson import ObjectId
from fastapi import Request
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager

from swiss_ai_hub.api.routes.event.event_controller import EventController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

ADMIN_ROLE = "TestOnlySpendAdmin"
ACME = "acme"
GLOBEX = "globex"


class _StubAuthHandler(AuthHandler):
    """Returns a caller-supplied identity so each test can vary sysadmin and tenant independently.

    `TestAuthHandler` fabricates one fixed identity, which cannot express the four cases here.
    Both `user_with_permission` and `sys_admin_user` resolve the user through `Depends(self.auth)`,
    so substituting the handler is enough to control every authorization input.
    """

    def __init__(self, user: UserIdentity):
        self._user = user

    async def __call__(self, request: Request) -> UserIdentity:
        return self._user

    async def authenticate_token(self, token: str, request: Request | None = None) -> UserIdentity:
        return self._user


def _identity(tenant_id: str | None, is_sys_admin: bool = False) -> UserIdentity:
    tenant = (
        TenantIdentity(id=tenant_id, name=tenant_id, access_rules=["aihub.admin.>"]) if tenant_id is not None else None
    )
    return UserIdentity(
        id=str(ObjectId()),
        name="Spend Tester",
        email="spend@example.com",
        roles=[ADMIN_ROLE],
        acting_within_tenant=tenant,
        is_sys_admin=is_sys_admin,
    )


@pytest.fixture(scope="function")
def mongodb():
    """Cleans up afterwards rather than connecting first: the app lifespan owns the connection for
    the duration of a test, so connecting here too would leave a stale default at teardown."""
    yield
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    PersistedAgentEventEntity.objects.delete()
    disconnect()


@pytest.fixture
def grant_admin_rules():
    """Map the test role onto `aihub.admin.>` without seeding role rows, as `role_mocks` does."""
    with patch.object(RoleEntity, "get_access_rules_for_roles", return_value={"aihub.admin.>"}):
        yield


def _client(user: UserIdentity) -> TestClient:
    runner = ApiTestRunner()
    runner.mount(EventController(auth=_StubAuthHandler(user)).get_llm_spend_by_user().get_llm_spend_by_tenant())
    return TestClient(runner.create_app(), raise_server_exceptions=True)


def _persist_cost_event(user_id: str, tenant_id: str | None, prompt: float) -> None:
    PersistedAgentEventEntity(
        agent_class="TestAgent",
        agent_id="test",
        thread_id="t_spend",
        display_id="disp",
        run_id="run",
        event_id=str(ObjectId()),
        event_type=AgentTopicManager.DISPLAY_EVENT,
        event_name="LLMCostEvent",
        event_data={
            "created_at": int(datetime.now(UTC).timestamp() * 1e9),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "prompt_tokens_costs": prompt,
            "completion_tokens_costs": 0.0,
        },
        event_parents=["LLMCostEvent", "CostEvent", "DisplayEvent"],
    ).save()


def _seed_two_tenants() -> None:
    """Called inside the client context: the app lifespan is what opens the DB connection."""
    _persist_cost_event("u_acme", ACME, 1.0)
    _persist_cost_event("u_globex", GLOBEX, 9.0)


class TestSpendByUserAuthorization:
    def test_tenant_admin_sees_only_their_own_tenant(self, mongodb, grant_admin_rules):
        with _client(_identity(ACME)) as client:
            _seed_two_tenants()
            response = client.get(f"/api/v1/{ACME}/events/spend/users")

        assert response.status_code == 200, response.text
        rows = response.json()
        assert [row["user_id"] for row in rows] == ["u_acme"]
        assert rows[0]["tenant_id"] == ACME

    def test_sysadmin_sees_every_tenant(self, mongodb, grant_admin_rules):
        with _client(_identity(ACME, is_sys_admin=True)) as client:
            _seed_two_tenants()
            response = client.get(f"/api/v1/{ACME}/events/spend/users")

        assert response.status_code == 200, response.text
        rows = {row["user_id"]: row for row in response.json()}
        assert set(rows) == {"u_acme", "u_globex"}
        # The cross-tenant view is the only place per-tenant spend is readable, so every row must
        # name its tenant rather than reporting the caller's or none at all.
        assert rows["u_acme"]["tenant_id"] == ACME
        assert rows["u_globex"]["tenant_id"] == GLOBEX

    def test_caller_without_an_acting_tenant_is_denied(self, mongodb, grant_admin_rules):
        """A null acting tenant must never mean "no filter".

        Denial currently comes from the permission dependency rather than the handler's own guard:
        `AccessChecker.from_user` yields empty rules when `acting_within_tenant` is None, so a
        non-sysadmin fails the service check first. The handler's 403 is defence in depth behind
        that — what matters here is that no path returns another tenant's rows.
        """
        with _client(_identity(None)) as client:
            _seed_two_tenants()
            response = client.get(f"/api/v1/{ACME}/events/spend/users")

        assert response.status_code == 403, response.text


class TestSpendByTenantAuthorization:
    def test_rejects_a_non_sysadmin(self, mongodb, grant_admin_rules):
        """A cross-tenant total is precisely the view one tenant must not have, however privileged
        they are inside their own."""
        with _client(_identity(ACME)) as client:
            _seed_two_tenants()
            response = client.get(f"/api/v1/{ACME}/events/spend/tenants")

        assert response.status_code == 403, response.text

    def test_allows_a_sysadmin(self, mongodb, grant_admin_rules):
        with _client(_identity(ACME, is_sys_admin=True)) as client:
            _seed_two_tenants()
            response = client.get(f"/api/v1/{ACME}/events/spend/tenants")

        assert response.status_code == 200, response.text
        rows = {row["tenant_id"]: row for row in response.json()}
        assert set(rows) == {ACME, GLOBEX}
        assert rows[GLOBEX]["total_costs"] == pytest.approx(9.0)
