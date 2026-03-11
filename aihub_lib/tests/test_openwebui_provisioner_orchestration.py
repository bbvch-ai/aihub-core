"""Tests for OpenWebuiProvisioner — top-level orchestration."""

from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture(autouse=True)
def _init_redis() -> None:
    mock_redis = MagicMock()
    mock_lock = MagicMock()
    mock_lock.acquire = AsyncMock(return_value=True)
    mock_lock.release = AsyncMock()
    mock_redis.lock.return_value = mock_lock
    OpenWebuiProvisioner.initialize(mock_redis)
    yield
    OpenWebuiProvisioner._redis = None  # type: ignore[assignment]


class TestProvision:
    @pytest.mark.asyncio
    async def test_provision_raises_on_step_failure(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner, "_sync_groups", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="boom"),
        ):
            await provisioner.provision()

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
