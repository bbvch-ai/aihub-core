"""An unreachable Milvus must not stop an agent container from starting.

Milvus turns its `/healthz` healthy long before the proxy accepts register, so `AgentRunner.start()`
regularly runs while Milvus still answers "Milvus Proxy is not ready yet". Letting that raise took
every agent container down and `restart: always` retried straight back into the same unready Milvus
- the loop that hit the API 56 times on staging 2026-09-03. The client only feeds the readiness
report (RAG opens its own connection through `MilvusVectorStoreConfig`), so losing it must cost a
false check, nothing more.
"""

from typing import ClassVar
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pymilvus.exceptions import MilvusException
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import StopEvent, UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner
from swiss_ai_hub.agent.workflow.decorators.step import step

RUNNER_MODULE = "swiss_ai_hub.agent.runners.agent_runner"


class _StartupReachedTheDispatcher(Exception):
    """Marks that start() got past the Milvus connection, so the rest of it need not be stood up."""


class _ChatAgent(Agent):
    name: ClassVar[LocaleString] = LocaleString(en="Chat Agent")
    description: ClassVar[LocaleString] = LocaleString(en="Answers messages")
    icon: ClassVar[str] = "mage:robot"

    @step()
    async def run(self, event: UserMessageEvent, displayer: EventDisplayer) -> StopEvent:
        return StopEvent()


@pytest.mark.asyncio
async def test_start_survives_an_unready_milvus_proxy():
    runner = AgentRunner(agent_type=_ChatAgent, agent_config=AgentConfig.as_form())

    with (
        patch(f"{RUNNER_MODULE}.NatsSettings.create_client", AsyncMock(return_value=MagicMock())),
        patch(f"{RUNNER_MODULE}.RedisSettings.create_client", MagicMock()),
        patch(
            f"{RUNNER_MODULE}.MilvusClient",
            side_effect=MilvusException(message="Milvus Proxy is not ready yet. please wait"),
        ),
        patch(f"{RUNNER_MODULE}.AgentDispatcher", side_effect=_StartupReachedTheDispatcher),
        pytest.raises(_StartupReachedTheDispatcher),
    ):
        await runner.start()

    assert runner.milvus_client is None


@pytest.mark.asyncio
async def test_readiness_reports_a_missing_milvus_client_as_unhealthy():
    """The degraded state has to stay visible, since the container no longer restarts to signal it."""
    runner = AgentRunner(agent_type=_ChatAgent, agent_config=AgentConfig.as_form())
    runner._loop = MagicMock()

    checks = runner.get_readiness_checks()

    assert runner.milvus_client is None
    assert checks.milvus is False


@pytest.mark.asyncio
async def test_start_survives_a_failure_outside_milvus_exception():
    """pymilvus re-raises the codes in its IGNORE_RETRY_CODES set as bare `grpc.RpcError`.

    An UNAUTHENTICATED from a token mismatch is therefore not a `MilvusException`, and naming that
    type in the handler would have left the crash loop reachable for a plain config drift.
    """
    runner = AgentRunner(agent_type=_ChatAgent, agent_config=AgentConfig.as_form())

    with (
        patch(f"{RUNNER_MODULE}.NatsSettings.create_client", AsyncMock(return_value=MagicMock())),
        patch(f"{RUNNER_MODULE}.RedisSettings.create_client", MagicMock()),
        patch(
            f"{RUNNER_MODULE}.MilvusClient",
            side_effect=RuntimeError("StatusCode.UNAUTHENTICATED, auth check failure"),
        ),
        patch(f"{RUNNER_MODULE}.AgentDispatcher", side_effect=_StartupReachedTheDispatcher),
        pytest.raises(_StartupReachedTheDispatcher),
    ):
        await runner.start()

    assert runner.milvus_client is None
