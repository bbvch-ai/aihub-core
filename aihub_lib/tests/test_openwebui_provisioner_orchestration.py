"""Tests for OpenWebuiProvisioner — top-level orchestration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.BASE_URL = "http://open-webui:8080"
    settings.API_KEY = MagicMock()
    settings.API_KEY.get_secret_value.return_value = "sk-test"
    return settings


@pytest.fixture
def provisioner(mock_settings: MagicMock) -> OpenWebuiProvisioner:
    return OpenWebuiProvisioner(settings=mock_settings)


class TestProvision:
    @pytest.mark.asyncio
    async def test_provision_calls_all_sync_steps(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner, "_sync_groups") as mock_groups,
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants") as mock_access,
        ):
            await provisioner.provision()

            mock_groups.assert_called_once()
            mock_models.assert_called_once()
            mock_access.assert_called_once()

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


class TestSyncAgents:
    @pytest.mark.asyncio
    async def test_sync_agents_calls_model_and_access_sync(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants") as mock_access,
        ):
            await provisioner.sync_agents([("rag", "default", "RAG Agent")])

            mock_models.assert_called_once()
            mock_access.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_agents_detects_changes(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants"),
        ):
            await provisioner.sync_agents([("rag", "default", "RAG Agent")])
            first_call_count = mock_models.call_count

            mock_models.reset_mock()
            await provisioner.sync_agents([("rag", "default", "RAG Agent"), ("llm", "v2", "LLM Agent")])

            assert first_call_count == 1
            mock_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_agents_skips_on_no_change(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner, "_sync_workspace_models") as mock_models,
            patch.object(provisioner, "_sync_access_grants"),
        ):
            await provisioner.sync_agents([("rag", "default", "RAG Agent")])
            mock_models.reset_mock()

            await provisioner.sync_agents([("rag", "default", "RAG Agent")])

            mock_models.assert_not_called()


class TestSyncAccess:
    @pytest.mark.asyncio
    async def test_sync_access_calls_group_and_access_sync(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch.object(provisioner, "_sync_groups") as mock_groups,
            patch.object(provisioner, "_sync_access_grants") as mock_access,
        ):
            await provisioner.sync_access()

            mock_groups.assert_called_once()
            mock_access.assert_called_once()
