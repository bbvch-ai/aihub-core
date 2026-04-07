"""Tests that only conversational agents are synced to OpenWebUI."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from swiss_ai_hub.core.infrastructure import OnlineAgent

from swiss_ai_hub.api.services.agent_endpoints_discovery_service import AgentEndpointsDiscoveryService


def _make_instance(agent_class: str, agent_id: str, name: str, *, is_conversational: bool) -> SimpleNamespace:
    return SimpleNamespace(agent_class=agent_class, agent_id=agent_id, name=name, is_conversational=is_conversational)


def _make_service() -> AgentEndpointsDiscoveryService:
    service = object.__new__(AgentEndpointsDiscoveryService)
    service._openwebui_provisioner = AsyncMock()
    return service


class TestOpenwebuiAgentFilter:
    @pytest.mark.asyncio
    async def test_only_conversational_agents_synced_to_openwebui(self) -> None:
        instances = [
            _make_instance("rag", "default", "RAG Agent", is_conversational=True),
            _make_instance("ingestion", "default", "Ingestion Worker", is_conversational=False),
            _make_instance("chat", "main", "Chat Agent", is_conversational=True),
        ]

        service = _make_service()
        await service._sync_agent_instances_to_openwebui(instances)

        service._openwebui_provisioner.sync_agents.assert_awaited_once()
        synced_agents = service._openwebui_provisioner.sync_agents.call_args[0][0]
        assert OnlineAgent(agent_class="rag", agent_id="default", display_name="RAG Agent") in synced_agents
        assert OnlineAgent(agent_class="chat", agent_id="main", display_name="Chat Agent") in synced_agents
        assert len(synced_agents) == 2

    @pytest.mark.asyncio
    async def test_no_agents_synced_when_all_non_conversational(self) -> None:
        instances = [
            _make_instance("ingestion", "default", "Ingestion Worker", is_conversational=False),
        ]

        service = _make_service()
        await service._sync_agent_instances_to_openwebui(instances)

        service._openwebui_provisioner.sync_agents.assert_awaited_once_with([])

    @pytest.mark.asyncio
    async def test_returns_false_on_provisioner_error(self) -> None:
        service = _make_service()
        service._openwebui_provisioner.sync_agents.side_effect = RuntimeError("not configured")

        result = await service._sync_agent_instances_to_openwebui([])
        assert result is False
