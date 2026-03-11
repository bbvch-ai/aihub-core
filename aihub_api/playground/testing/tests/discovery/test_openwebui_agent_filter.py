"""Tests that only conversational agents are synced to OpenWebUI."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from aihub_lib.infrastructure.openwebui.OnlineAgent import OnlineAgent

from aihub_api.services.AgentEndpointsDiscoveryService import AgentEndpointsDiscoveryService


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

        with patch("aihub_api.services.AgentEndpointsDiscoveryService.OpenWebuiProvisioner") as mock_provisioner_cls:
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

        with patch("aihub_api.services.AgentEndpointsDiscoveryService.OpenWebuiProvisioner") as mock_provisioner_cls:
            mock_provisioner = AsyncMock()
            mock_provisioner_cls.return_value = mock_provisioner

            await AgentEndpointsDiscoveryService._sync_agent_instances_to_openwebui(instances)

            mock_provisioner.sync_agents.assert_awaited_once_with([])
