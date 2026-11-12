"""A client may send the user's own Keycloak token as X-AIHub-User-Token so an MCP agent profile with auth_mode
'user_token' can call its server as that user. The agent endpoints the OpenWebUI pipe streams to and the OpenAI-style
completions the Admin UI calls accept it only when it is the requesting user's own (#2451)."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import TEST_USER_OID

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

AGENT_CLASS = "forwarded_token_agent"
AGENT_ID = "forwarded_token_agent_1"
SEND = f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/StartEvent"
COMPLETIONS = "/openai/chat/completions"
DECODE_TOKEN = (
    "swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler.KeycloakAuthHandler.decode_token"
)

AGENT_REQUESTS = [
    pytest.param("POST", SEND, {}, id="agent-endpoint"),
    pytest.param("POST", SEND + "/stream", {}, id="agent-stream-endpoint"),
    pytest.param(
        "POST",
        COMPLETIONS,
        {"model": f"{AGENT_CLASS}/{AGENT_ID}", "messages": [{"role": "user", "content": "Hello"}], "stream": False},
        id="openai-completions",
    ),
]


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client() -> AsyncGenerator[AsyncClient]:
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(AgentController(auth=TestAuthHandler()).get_agent_instance())
    runner.mount(OpenaiController(auth=TestAuthHandler()).chat_completion_with_assistants())
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
def keycloak_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KEYCLOAK_URL", "http://keycloak.test")


def _token_of(monkeypatch: pytest.MonkeyPatch, sub: str) -> None:
    async def decode(_self: Any, _token: str, **_: Any) -> dict[str, str]:
        return {"sub": sub}

    monkeypatch.setattr(DECODE_TOKEN, decode)


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(("method", "path", "body"), AGENT_REQUESTS)
async def test_a_token_that_is_not_a_keycloak_token_is_refused(api_client, method, path, body) -> None:
    response = await api_client.request(method, path, json=body, headers={"X-AIHub-User-Token": "not-a-jwt"})

    assert response.status_code == 401, response.text


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(("method", "path", "body"), AGENT_REQUESTS)
async def test_another_users_token_is_refused(api_client, monkeypatch, method, path, body) -> None:
    _token_of(monkeypatch, "someone-else")

    response = await api_client.request(method, path, json=body, headers={"X-AIHub-User-Token": "eyJ.someone-else"})

    assert response.status_code == 401, response.text
    assert "eyJ.someone-else" not in response.text


@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize(("method", "path", "body"), AGENT_REQUESTS)
async def test_the_requesting_users_own_token_is_accepted(api_client, monkeypatch, method, path, body) -> None:
    _token_of(monkeypatch, TEST_USER_OID)

    response = await api_client.request(method, path, json=body, headers={"X-AIHub-User-Token": "eyJ.own"})

    assert response.status_code == 200, response.text
