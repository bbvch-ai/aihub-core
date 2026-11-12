"""A sysadmin arriving through OpenWebUI's signed headers gets the chat's user access, never the sysadmin bypass."""

import pytest

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.access.access_level import AccessLevel
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

pytestmark = pytest.mark.asyncio

TENANT_CEILING = ["aihub.user.service.>", "aihub.admin.agent.RAGAgent.hr-bot"]
ROLE_RULES = {"HrBotAdmin": {"aihub.admin.agent.RAGAgent.hr-bot"}}


@pytest.fixture(autouse=True)
def role_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    async def rules_of(role_names: list[str], tenant_id: str) -> set[str]:
        return {rule for name in role_names for rule in ROLE_RULES.get(name, set())}

    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", staticmethod(rules_of))


def _user(roles: list[str], openwebui_sys_admin: bool) -> UserIdentity:
    return UserIdentity(
        id="user-1",
        name="Alice",
        email="alice@example.com",
        roles=roles,
        acting_within_tenant=TenantIdentity(id="tenant-1", name="acme", access_rules=TENANT_CEILING),
        openwebui_sys_admin=openwebui_sys_admin,
    )


async def test_gives_user_access_to_what_the_tenant_offers() -> None:
    checker = await AccessChecker.from_user(_user(roles=[], openwebui_sys_admin=True))

    assert not checker.is_sys_admin
    assert checker.has_access_to_service("agent")
    assert checker.access_level_for_agent("RAGAgent", "hr-bot") == AccessLevel.ACCESS_USER


async def test_stays_under_the_tenant_ceiling() -> None:
    checker = await AccessChecker.from_user(_user(roles=[], openwebui_sys_admin=True))

    assert checker.access_level_for_agent("RAGAgent", "blocked-bot") == AccessLevel.ACCESS_DENIED


async def test_grants_no_admin_rights() -> None:
    checker = await AccessChecker.from_user(_user(roles=[], openwebui_sys_admin=True))

    assert checker.access_level("aihub.admin.agent.RAGAgent.hr-bot") == AccessLevel.ACCESS_DENIED


async def test_keeps_the_admin_rights_of_the_users_own_roles() -> None:
    checker = await AccessChecker.from_user(_user(roles=["HrBotAdmin"], openwebui_sys_admin=True))

    assert checker.access_level("aihub.admin.agent.RAGAgent.hr-bot") == AccessLevel.ACCESS_ADMIN


async def test_a_user_without_the_mark_and_without_roles_gets_nothing() -> None:
    checker = await AccessChecker.from_user(_user(roles=[], openwebui_sys_admin=False))

    assert checker.access_level_for_agent("RAGAgent", "hr-bot") == AccessLevel.ACCESS_DENIED
