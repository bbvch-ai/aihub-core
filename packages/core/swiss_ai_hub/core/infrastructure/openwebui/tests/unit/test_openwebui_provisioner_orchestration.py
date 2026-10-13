"""Tests for OpenWebuiProvisioner — top-level orchestration."""

from unittest.mock import patch

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import (
    RETRIEVAL_SETTINGS,
    OpenWebuiProvisioner,
)

_RAG_AGENT = OnlineAgent(agent_class="rag", agent_id="default", display_name="RAG Agent")


class TestProvision:
    @pytest.mark.asyncio
    async def test_provision_raises_on_step_failure(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner._openwebui, "update_retrieval_config"),
            patch.object(provisioner, "_sync_groups", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="boom"),
        ):
            await provisioner.provision()

    @pytest.mark.asyncio
    async def test_provision_uses_known_online_agents(self, provisioner: OpenWebuiProvisioner) -> None:
        """Startup provisioning queries DB for known online agents to seed workspace models."""
        with (
            patch.object(provisioner._openwebui, "update_retrieval_config"),
            patch.object(provisioner, "_sync_groups"),
            patch.object(provisioner, "_get_known_online_agents", return_value=[_RAG_AGENT]) as mock_known,
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_get_available_llm_models", return_value=[]),
            patch.object(provisioner, "_sync_llm_workspace_models"),
            patch.object(provisioner, "_sync_access_grants"),
            patch.object(provisioner, "_sync_knowledge_entries"),
        ):
            await provisioner.provision()

            mock_known.assert_called_once()
            online_agents = mock_models.call_args[0][1]
            assert online_agents == [_RAG_AGENT]

    @pytest.mark.asyncio
    async def test_provision_enforces_that_uploads_are_not_embedded(self, provisioner: OpenWebuiProvisioner) -> None:
        """OpenWebUI prefers its stored config over the compose env var, so the API has to set it on every run."""
        with (
            patch.object(provisioner._openwebui, "update_retrieval_config") as mock_config,
            patch.object(provisioner, "_sync_groups"),
            patch.object(provisioner, "_get_known_online_agents", return_value=[]),
            patch.object(provisioner, "_sync_workspace_models"),
            patch.object(provisioner, "_get_available_llm_models", return_value=[]),
            patch.object(provisioner, "_sync_llm_workspace_models"),
            patch.object(provisioner, "_sync_access_grants"),
            patch.object(provisioner, "_sync_knowledge_entries"),
        ):
            await provisioner.provision()

            assert mock_config.call_args[0][1] == RETRIEVAL_SETTINGS
            assert RETRIEVAL_SETTINGS["BYPASS_EMBEDDING_AND_RETRIEVAL"] is True


class TestSyncAgents:
    @pytest.mark.asyncio
    async def test_sync_agents_always_syncs(self, provisioner: OpenWebuiProvisioner) -> None:
        """Change detection is handled by AgentEndpointsDiscoveryService, not the provisioner."""
        with (
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants"),
            patch.object(provisioner, "_sync_knowledge_entries"),
        ):
            await provisioner.sync_agents([_RAG_AGENT])
            await provisioner.sync_agents([_RAG_AGENT])

            assert mock_models.call_count == 2
