from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner


class TestProvision:
    @pytest.mark.asyncio
    async def test_provision_calls_all_sync_methods(self, provisioner: OpenWebuiProvisioner):
        mock_redis = MagicMock()
        mock_lock = AsyncMock()
        mock_lock.acquire = AsyncMock(return_value=True)
        mock_lock.release = AsyncMock()
        mock_redis.lock.return_value = mock_lock
        OpenWebuiProvisioner._redis = mock_redis

        with (
            patch.object(provisioner, "_sync_groups", new_callable=AsyncMock) as mock_groups,
            patch.object(provisioner, "_sync_workspace_models", new_callable=AsyncMock) as mock_models,
            patch.object(provisioner, "_sync_access_grants", new_callable=AsyncMock) as mock_access,
        ):
            await provisioner.provision()

            mock_groups.assert_called_once()
            mock_models.assert_called_once()
            mock_access.assert_called_once()


class TestSyncAgents:
    @pytest.mark.asyncio
    async def test_sync_agents_syncs_models_and_access(self, provisioner: OpenWebuiProvisioner):
        mock_redis = MagicMock()
        mock_lock = AsyncMock()
        mock_lock.acquire = AsyncMock(return_value=True)
        mock_lock.release = AsyncMock()
        mock_redis.lock.return_value = mock_lock
        OpenWebuiProvisioner._redis = mock_redis

        with (
            patch.object(provisioner, "_sync_workspace_models", new_callable=AsyncMock) as mock_models,
            patch.object(provisioner, "_sync_access_grants", new_callable=AsyncMock) as mock_access,
        ):
            await provisioner.sync_agents([])

            mock_models.assert_called_once()
            mock_access.assert_called_once()


class TestSyncAccess:
    @pytest.mark.asyncio
    async def test_sync_access_syncs_groups_and_grants(self, provisioner: OpenWebuiProvisioner):
        mock_redis = MagicMock()
        mock_lock = AsyncMock()
        mock_lock.acquire = AsyncMock(return_value=True)
        mock_lock.release = AsyncMock()
        mock_redis.lock.return_value = mock_lock
        OpenWebuiProvisioner._redis = mock_redis

        with (
            patch.object(provisioner, "_sync_groups", new_callable=AsyncMock) as mock_groups,
            patch.object(provisioner, "_sync_access_grants", new_callable=AsyncMock) as mock_access,
        ):
            await provisioner.sync_access()

            mock_groups.assert_called_once()
            mock_access.assert_called_once()
