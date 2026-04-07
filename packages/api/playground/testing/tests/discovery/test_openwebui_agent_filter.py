"""Tests that only conversational agents are synced to OpenWebUI."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from swiss_ai_hub.core.infrastructure import OnlineAgent

from swiss_ai_hub.api.services.agent_endpoints_discovery_service import AgentEndpointsDiscoveryService


def _make_instance(agent_class: str, agent_id: str, name: str, *, is_conversational: bool) -> SimpleNamespace:
    return SimpleNamespace(agent_class=agent_class, agent_id=agent_id, name=name, is_conversational=is_conversational)


class TestOpenwebuiAgentFilter:
    @pytest.mark.asyncio
    async def test_only_conversational_agents_synced_to_openwebui(self) -> None:
        instances = [
            _make_instance("rag", "default", "RAG Agent", is_conversational=True),
            _make_instance("ingestion", "default", "Ingestion Worker", is_conversational=False),
            _make_instance("chat", "main", "Chat Agent", is_conversational=True),
        ]

        with patch(
            "swiss_ai_hub.api.services.agent_endpoints_discovery_service.OpenWebuiProvisioner"
        ) as mock_provisioner_cls:
            mock_provisioner = AsyncMock()
            mock_provisioner_cls.return_value = mock_provisioner

            await AgentEndpointsDiscoveryService._sync_agent_instances_to_openwebui(instances)

            mock_provisioner.sync_agents.assert_awaited_once()
            synced_agents = mock_provisioner.sync_agents.call_args[0][0]
            assert OnlineAgent(agent_class="rag", agent_id="default", display_name="RAG Agent") in synced_agents
            assert OnlineAgent(agent_class="chat", agent_id="main", display_name="Chat Agent") in synced_agents
            assert len(synced_agents) == 2

    @pytest.mark.asyncio
    async def test_no_agents_synced_when_all_non_conversational(self) -> None:
        instances = [
            _make_instance("ingestion", "default", "Ingestion Worker", is_conversational=False),
        ]

        with patch(
            "swiss_ai_hub.api.services.agent_endpoints_discovery_service.OpenWebuiProvisioner"
        ) as mock_provisioner_cls:
            mock_provisioner = AsyncMock()
            mock_provisioner_cls.return_value = mock_provisioner

            await AgentEndpointsDiscoveryService._sync_agent_instances_to_openwebui(instances)

            mock_provisioner.sync_agents.assert_awaited_once_with([])

    @pytest.mark.asyncio
    async def test_returns_false_on_provisioner_error(self) -> None:
        with patch(
            "swiss_ai_hub.api.services.agent_endpoints_discovery_service.OpenWebuiProvisioner"
        ) as mock_provisioner_cls:
            mock_provisioner_cls.side_effect = RuntimeError("not configured")

            result = await AgentEndpointsDiscoveryService._sync_agent_instances_to_openwebui([])
            assert result is False
