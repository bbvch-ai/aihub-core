from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

_RAG_AGENT = OnlineAgent(agent_class="rag", agent_id="default", display_name="RAG Agent")


def _make_lock(*, acquired: bool) -> MagicMock:
    lock = MagicMock()
    lock.acquire = AsyncMock(return_value=acquired)
    lock.release = AsyncMock()
    return lock


def _setup_redis(provisioner: OpenWebuiProvisioner, *, acquired: bool) -> MagicMock:
    mock_redis = MagicMock()
    mock_redis.lock.return_value = _make_lock(acquired=acquired)
    OpenWebuiProvisioner._redis = mock_redis
    return mock_redis


class TestSyncAgentsLocking:
    @pytest.mark.asyncio
    async def test_skipped_when_lock_held(self, provisioner: OpenWebuiProvisioner) -> None:
        _setup_redis(provisioner, acquired=False)

        with patch.object(provisioner, "_sync_workspace_models") as mock_models:
            await provisioner.sync_agents([_RAG_AGENT])
            mock_models.assert_not_called()

    @pytest.mark.asyncio
    async def test_lock_released_after_sync(self, provisioner: OpenWebuiProvisioner) -> None:
        redis = _setup_redis(provisioner, acquired=True)

        with (
            patch.object(provisioner, "_sync_workspace_models", new_callable=AsyncMock),
            patch.object(provisioner, "_sync_access_grants", new_callable=AsyncMock),
        ):
            await provisioner.sync_agents([_RAG_AGENT])
            redis.lock.return_value.release.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lock_released_on_exception(self, provisioner: OpenWebuiProvisioner) -> None:
        redis = _setup_redis(provisioner, acquired=True)

        with (
            patch.object(provisioner, "_sync_workspace_models", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="boom"),
        ):
            await provisioner.sync_agents([_RAG_AGENT])

        redis.lock.return_value.release.assert_awaited_once()


class TestSyncAccessLocking:
    @pytest.mark.asyncio
    async def test_skipped_when_lock_held(self, provisioner: OpenWebuiProvisioner) -> None:
        _setup_redis(provisioner, acquired=False)

        with patch.object(provisioner, "_sync_groups") as mock_groups:
            await provisioner.sync_access()
            mock_groups.assert_not_called()

    @pytest.mark.asyncio
    async def test_lock_released_after_sync(self, provisioner: OpenWebuiProvisioner) -> None:
        redis = _setup_redis(provisioner, acquired=True)

        with (
            patch.object(provisioner, "_sync_groups", new_callable=AsyncMock),
            patch.object(provisioner, "_sync_access_grants", new_callable=AsyncMock),
        ):
            await provisioner.sync_access()
            redis.lock.return_value.release.assert_awaited_once()


class TestProvisionLocking:
    @pytest.mark.asyncio
    async def test_skipped_when_lock_held(self, provisioner: OpenWebuiProvisioner) -> None:
        _setup_redis(provisioner, acquired=False)

        with patch.object(provisioner, "_sync_groups") as mock_groups:
            await provisioner.provision()
            mock_groups.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_when_not_initialized(self, provisioner: OpenWebuiProvisioner) -> None:
        OpenWebuiProvisioner._redis = None

        with pytest.raises(RuntimeError, match="not initialized"):
            await provisioner.provision()
