"""Covers who may read, change and post into a thread, through every thread and event endpoint.

Every caller except the narrow process users holds ``aihub.user.>``, the grant every ordinary user has. That grant
matched the ``process.None.None`` permission built for a thread without a process, which opened every chat to every
user of every tenant (aihub-core-private#377). Asserted through HTTP rather than against ``ThreadAccess``, so an
endpoint that stops calling it fails here.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from bson import ObjectId
from fastapi import Request
from httpx import ASGITransport, AsyncClient, Response
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.routes.event.event_controller import EventController
from swiss_ai_hub.api.routes.event.event_service import EventService
from swiss_ai_hub.api.routes.thread.thread_controller import ThreadController
from swiss_ai_hub.api.routes.user.dto.minimal_user_dto import MinimalUserDTO
from swiss_ai_hub.api.routes.user.user_service import UserService
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

AGENT_CLASS = "thread_access_agent"
AGENT_ID = "thread_access_agent_1"
AGENT = AgentInstanceRef(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
DISPLAY_ID = str(ObjectId())
SEND = f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/StartEvent"
USER_HEADER = "X-Test-User"

MEMBER = "member"
NEIGHBOUR = "neighbour"
OUTSIDER = "outsider"
SYSADMIN = "sysadmin"
PROCESS_USER = "process-user"
OTHER_PROCESS_USER = "other-process-user"

_TENANT_CEILING = ["aihub.admin.>"]
# Per caller: role, tenant, sysadmin. Only the member belongs to the threads below.
_CALLERS = {
    MEMBER: ("AIHubUser", "tenant-a", False),
    NEIGHBOUR: ("AIHubUser", "tenant-a", False),
    OUTSIDER: ("AIHubUser", "tenant-b", False),
    SYSADMIN: ("AIHubUser", "tenant-b", True),
    PROCESS_USER: ("InvoiceProcessUser", "tenant-a", False),
    OTHER_PROCESS_USER: ("OtherInvoiceProcessUser", "tenant-a", False),
}
_ROLE_RULES = {
    "AIHubUser": {"aihub.user.>"},
    # The agent rule lets the posts below pass the endpoint guard, so only the thread can refuse them.
    "InvoiceProcessUser": {
        "aihub.user.service.>",
        f"aihub.user.agent.{AGENT_CLASS}.{AGENT_ID}",
        "aihub.user.process.InvoiceProcess.p1",
    },
    "OtherInvoiceProcessUser": {"aihub.user.service.>", "aihub.user.process.InvoiceProcess.p2"},
}

READS = [
    ("GET", "/threads/{thread_id}", None),
    ("GET", "/threads/{thread_id}/open-chat-hitl", None),
    ("GET", "/events/agents/threads/{thread_id}", None),
    ("GET", f"/events/agents/displays/{DISPLAY_ID}/thread", None),
    ("GET", "/events/agents/timeseries/24h?thread_id={thread_id}", None),
]
CHANGES = [
    ("POST", "/threads/{thread_id}/agents", {"agent_class": AGENT_CLASS, "agent_id": AGENT_ID}),
    ("DELETE", f"/threads/{{thread_id}}/agents/{AGENT_CLASS}/{AGENT_ID}", None),
    ("POST", "/threads/{thread_id}/users", {"user_id": OUTSIDER}),
    ("DELETE", f"/threads/{{thread_id}}/users/{MEMBER}", None),
]
POSTS = [
    ("POST", SEND + "?thread_id={thread_id}", {}),
    ("POST", SEND + "/stream?thread_id={thread_id}", {}),
]
DOWNLOAD = [("GET", "/threads/{thread_id}/extracted-tables/any/download-url", None)]


class _CallerAuthHandler(AuthHandler):
    """Acts as whichever caller the request names, so one app serves them all."""

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        caller = request.headers[USER_HEADER]
        role, tenant_id, is_sys_admin = _CALLERS[caller]
        return UserIdentity(
            id=caller,
            name=caller,
            email=f"{caller}@example.com",
            roles=[role],
            acting_within_tenant=TenantIdentity(id=tenant_id, name=tenant_id, access_rules=_TENANT_CEILING),
            is_sys_admin=is_sys_admin,
        )


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client() -> AsyncGenerator[AsyncClient]:
    auth = _CallerAuthHandler()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(AgentController(auth=auth).get_agent_instance())
    runner.mount(
        ThreadController(auth=auth)
        .create_thread()
        .get_thread()
        .get_open_chat_hitl()
        .get_extracted_table_download_url()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread()
    )
    runner.mount(
        EventController(auth=auth)
        .get_agent_events_in_thread()
        .resolve_thread_for_display()
        .get_agent_event_timeseries()
    )
    await runner.start_simulation()
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        await runner.create_agent_config_in_db()
        async with AsyncClient(
            transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1/active"
        ) as client:
            yield client
    await runner.stop_simulation()


@pytest.fixture(autouse=True)
def _rules_and_users(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rules come from the callers' roles alone, and members resolve without Keycloak."""

    async def _rules(roles: list[str], tenant_id: str) -> set[str]:
        return set().union(*(_ROLE_RULES[r] for r in roles))

    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", _rules)

    async def _user(user_oid: str) -> MinimalUserDTO:
        return MinimalUserDTO(id=user_oid, name=user_oid, email=f"{user_oid}@example.com")

    monkeypatch.setattr(UserService, "get_user_by_oid", staticmethod(_user))


def _owning_display(monkeypatch: pytest.MonkeyPatch, thread: ThreadEntity) -> None:
    monkeypatch.setattr(EventService, "thread_id_for_display", staticmethod(lambda display_id: str(thread.id)))


@pytest_asyncio.fixture(loop_scope="module")
async def chat_thread(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[ThreadEntity]:
    thread = await ThreadEntity.create_thread("chat", users=[User(user_id=MEMBER)], agents=[AGENT])
    _owning_display(monkeypatch, thread)
    yield thread
    await thread.delete()


@pytest_asyncio.fixture(loop_scope="module")
async def process_thread(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[ThreadEntity]:
    thread = await ThreadEntity.create_process_thread(
        "Invoice review",
        AGENT,
        ObjectId(),
        process_class="InvoiceProcess",
        process_id="p1",
        process_walkthrough_id="w1",
    )
    _owning_display(monkeypatch, thread)
    yield thread
    await thread.delete()


async def _call(client: AsyncClient, caller: str, endpoint: tuple, thread: ThreadEntity) -> Response:
    method, path, body = endpoint
    return await client.request(method, path.format(thread_id=thread.id), json=body, headers={USER_HEADER: caller})


async def _members_and_agents(thread: ThreadEntity) -> tuple[list[str], list[tuple[str, str]]]:
    stored = await ThreadEntity.get_thread_by_id(str(thread.id))
    return [user.user_id for user in stored.users], [(agent.agent_class, agent.agent_id) for agent in stored.agents]


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("caller", [NEIGHBOUR, OUTSIDER])
@pytest.mark.parametrize("endpoint", READS + CHANGES + POSTS + DOWNLOAD)
async def test_a_non_member_is_refused_a_chat_thread(api_client, chat_thread, caller, endpoint):
    """The neighbour shares the member's tenant, the outsider does not; both hold `aihub.user.>`."""
    before = await _members_and_agents(chat_thread)

    response = await _call(api_client, caller, endpoint, chat_thread)

    assert response.status_code == 403, response.text
    assert await _members_and_agents(chat_thread) == before


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("caller", [MEMBER, SYSADMIN])
@pytest.mark.parametrize("endpoint", READS)
async def test_the_member_and_a_sysadmin_read_a_chat_thread(api_client, chat_thread, caller, endpoint):
    response = await _call(api_client, caller, endpoint, chat_thread)

    assert response.status_code == 200, response.text


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("endpoint", READS)
async def test_a_user_with_access_to_the_process_reads_its_thread(api_client, process_thread, endpoint):
    """Process threads have no members, so process access is the only way anyone but a sysadmin reads them."""
    response = await _call(api_client, PROCESS_USER, endpoint, process_thread)

    assert response.status_code == 200, response.text


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("endpoint", READS + DOWNLOAD)
async def test_a_user_with_access_to_another_process_is_refused_its_thread(api_client, process_thread, endpoint):
    response = await _call(api_client, OTHER_PROCESS_USER, endpoint, process_thread)

    assert response.status_code == 403, response.text


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("endpoint", CHANGES + POSTS)
async def test_access_to_the_process_does_not_allow_changing_or_posting_into_its_thread(
    api_client, process_thread, endpoint
):
    before = await _members_and_agents(process_thread)

    response = await _call(api_client, PROCESS_USER, endpoint, process_thread)

    assert response.status_code == 403, response.text
    assert await _members_and_agents(process_thread) == before


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("agent_id", ["a.b", "*", "a b"])
@pytest.mark.parametrize("request_of", ["add_agent", "create_thread"])
async def test_a_malformed_agent_reference_is_invalid_input(api_client, chat_thread, request_of, agent_id):
    """The access check raises on a dot, a wildcard or a space instead of denying, so the body is refused first."""
    agent = {"agent_class": AGENT_CLASS, "agent_id": agent_id}
    method, path, body = {
        "add_agent": ("POST", "/threads/{thread_id}/agents", agent),
        "create_thread": ("POST", "/threads/", {"name": "chat", "agents": [agent]}),
    }[request_of]

    response = await _call(api_client, MEMBER, (method, path, body), chat_thread)

    assert response.status_code == 422, response.text
