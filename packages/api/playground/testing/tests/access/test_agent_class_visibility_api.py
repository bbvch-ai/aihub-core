"""Covers which blueprints a tenant sees on the agent-class list.

The route guard is an existence query — any single ``aihub.user.agent.*`` rule satisfies it — so the
per-class filter inside the endpoint is the only thing standing between a curated tenant and the whole
blueprint catalog. Asserted through the HTTP response rather than against ``AccessChecker`` directly, so a
refactor that moves the filter out of the controller cannot quietly drop it.
"""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from swiss_ai_hub.core.agents import WorkflowGraph
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.form import ConfigSpecs, TemplateData
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.routes.agent.agent_service import AgentService
from swiss_ai_hub.api.routes.agent.dto.agent_class_dto import AgentClassDTO
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

ROUTE = "/api/v1/customer-tenant/agents/classes"

_STANDARD = ("LLMWrappingAgent", "FewShotAgent", "RAGAgent")
_OPTIONAL = ("ExpertRAGAgent", "EmailClassificationAgent")
# A playground class discovered on a dev machine once: nothing ever deletes ``agent_classes`` rows, so
# the catalog serves it forever and it has to be curated out like any other blueprint.
_STALE = ("ConditionalAgent",)

_ALL_DISCOVERED = _STANDARD + _OPTIONAL + _STALE

# What the derivation emits for every rule family other than agents and models. The service rule matters
# here: the controller's own service gate runs before any per-class filtering, so a ceiling without it is
# rejected outright and would never exercise the filter under test.
_NON_AGENT_CEILING = [
    "aihub.admin.knowledge",
    "aihub.admin.knowledge.>",
    "aihub.admin.process.>",
    "aihub.admin.service.>",
    "aihub.user.memory.>",
]

_STANDARD_CEILING = [*_NON_AGENT_CEILING, *(f"aihub.admin.agent.{agent_class}.>" for agent_class in _STANDARD)]


def _agent_class(agent_class: str) -> AgentClassDTO:
    """A blueprint carrying one template, so the response can be checked for template loss too."""
    return AgentClassDTO(
        agent_class=agent_class,
        name=LocaleString(en=agent_class),
        description=LocaleString(en=f"{agent_class} description"),
        form=[],
        agent_config_specs=ConfigSpecs(config_class=agent_class, config_schema={}),
        start_events=[],
        stop_events=[],
        hitl_request_events=[],
        hitl_response_events=[],
        network_graph=WorkflowGraph(nodes=[], links=[]),
        is_conversational=True,
        templates=[
            TemplateData(
                name=LocaleString(en=f"{agent_class} starter"),
                description=LocaleString(en="A starter profile"),
            )
        ],
    )


class _AuthHandler(AuthHandler):
    """A tenant admin whose tenant ceiling is the thing under test."""

    def __init__(self, *, tenant_access_rules: list[str], is_sys_admin: bool = False) -> None:
        self._tenant_access_rules = tenant_access_rules
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
                id="customer-tenant", name="Customer Tenant", access_rules=list(self._tenant_access_rules)
            ),
            is_sys_admin=self._is_sys_admin,
        )


@pytest.fixture(autouse=True)
def _stub_catalog_and_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    """The role grants everything, so whatever is denied below is denied by the ceiling alone."""
    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", lambda roles, tenant_id: {"aihub.admin.>"})

    async def _classes(t: LocaleHandler, online: bool | None = None) -> list[AgentClassDTO]:
        return [_agent_class(agent_class) for agent_class in _ALL_DISCOVERED]

    monkeypatch.setattr(AgentService, "get_agent_classes", _classes)


def _returned_classes(*, tenant_access_rules: list[str], is_sys_admin: bool = False) -> list[str]:
    runner = ApiTestRunner()
    runner.mount(
        AgentController(
            auth=_AuthHandler(tenant_access_rules=tenant_access_rules, is_sys_admin=is_sys_admin)
        ).get_agent_classes()
    )
    response = TestClient(runner.create_app()).get(ROUTE)

    assert response.status_code == 200, response.text
    return [entry["agent_class"] for entry in response.json()]


def test_a_curated_tenant_sees_only_its_standard_blueprints() -> None:
    assert sorted(_returned_classes(tenant_access_rules=_STANDARD_CEILING)) == sorted(_STANDARD)


def test_the_optional_and_stale_blueprints_are_withheld() -> None:
    """Separated from the assertion above so a failure names what leaked rather than just a length."""
    returned = _returned_classes(tenant_access_rules=_STANDARD_CEILING)

    for withheld in _OPTIONAL + _STALE:
        assert withheld not in returned, withheld


def test_a_wildcard_tenant_still_sees_every_blueprint() -> None:
    """Existing tenants keep ``aihub.admin.agent.>``, so the filter must be a no-op for them."""
    assert sorted(_returned_classes(tenant_access_rules=[*_NON_AGENT_CEILING, "aihub.admin.agent.>"])) == sorted(
        _ALL_DISCOVERED
    )


def test_a_sysadmin_bypasses_the_ceiling() -> None:
    assert sorted(_returned_classes(tenant_access_rules=_STANDARD_CEILING, is_sys_admin=True)) == sorted(
        _ALL_DISCOVERED
    )


def test_a_tenant_granted_one_extra_blueprint_sees_it() -> None:
    """The "add one for a customer" path: granting the class is all it takes, with no redeploy."""
    returned = _returned_classes(
        tenant_access_rules=[*_STANDARD_CEILING, "aihub.admin.agent.EmailClassificationAgent.>"]
    )

    assert "EmailClassificationAgent" in returned
    assert "ExpertRAGAgent" not in returned


def test_curation_withholds_blueprints_and_never_their_templates() -> None:
    """Curation is per blueprint; a blueprint a tenant can see keeps every template it publishes."""
    runner = ApiTestRunner()
    runner.mount(AgentController(auth=_AuthHandler(tenant_access_rules=_STANDARD_CEILING)).get_agent_classes())
    response = TestClient(runner.create_app()).get(ROUTE)

    assert response.status_code == 200, response.text
    for entry in response.json():
        assert [template["name"]["en"] for template in entry["templates"]] == [f"{entry['agent_class']} starter"]
