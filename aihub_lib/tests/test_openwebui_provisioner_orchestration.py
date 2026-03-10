from unittest.mock import MagicMock, patch

import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.BASE_URL = "http://open-webui:8080"
    settings.SECRET_KEY = MagicMock()
    settings.SECRET_KEY.get_secret_value.return_value = "sk-test"
    settings.SCIM_TOKEN = MagicMock()
    settings.SCIM_TOKEN.get_secret_value.return_value = "scim-test"
    return settings


@pytest.fixture
def provisioner(mock_settings: MagicMock) -> OpenWebuiProvisioner:
    return OpenWebuiProvisioner(settings=mock_settings)


class TestProvision:
    @pytest.mark.asyncio
    async def test_provision_continues_after_step_failure(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner, "_sync_groups", side_effect=RuntimeError("boom")),
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants") as mock_access,
        ):
            await provisioner.provision()

            mock_models.assert_called_once()
            mock_access.assert_called_once()

    @pytest.mark.asyncio
    async def test_provision_passes_empty_agents_for_clean_slate(self, provisioner: OpenWebuiProvisioner) -> None:
        """Startup provisioning passes no agents — models are re-created by sync_agents after discovery."""
        with (
            patch.object(provisioner, "_sync_groups"),
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants"),
        ):
            await provisioner.provision()

            online_agents = mock_models.call_args[0][1]
            assert online_agents == []


class TestSyncAgents:
    @pytest.mark.asyncio
    async def test_sync_agents_always_syncs(self, provisioner: OpenWebuiProvisioner) -> None:
        """Change detection is handled by AgentEndpointsDiscoveryService, not the provisioner."""
        with (
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants"),
        ):
            await provisioner.sync_agents([("rag", "default", "RAG Agent")])
            await provisioner.sync_agents([("rag", "default", "RAG Agent")])

            assert mock_models.call_count == 2
