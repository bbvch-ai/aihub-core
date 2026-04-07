"""Tests for OpenWebuiProvisioner distributed locking."""

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


@pytest.fixture
def mock_redis() -> MagicMock:
    return MagicMock()


@pytest.fixture(autouse=True)
def _init_redis(mock_redis: MagicMock) -> None:
    mock_redis.lock.return_value = _make_lock(acquired=True)
    OpenWebuiProvisioner.initialize(mock_redis)
    yield
    OpenWebuiProvisioner._redis = None  # type: ignore[assignment]


class TestDistributedLocking:
    @pytest.mark.asyncio
    async def test_sync_agents_skipped_when_lock_held(
        self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock
    ) -> None:
        mock_redis.lock.return_value = _make_lock(acquired=False)

        with patch.object(provisioner, "_sync_workspace_models") as mock_models:
            await provisioner.sync_agents([_RAG_AGENT])
            mock_models.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_access_skipped_when_lock_held(
        self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock
    ) -> None:
        mock_redis.lock.return_value = _make_lock(acquired=False)

        with patch.object(provisioner, "_sync_groups") as mock_groups:
            await provisioner.sync_access()
            mock_groups.assert_not_called()

    @pytest.mark.asyncio
    async def test_provision_skipped_when_lock_held(
        self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock
    ) -> None:
        mock_redis.lock.return_value = _make_lock(acquired=False)

        with patch.object(provisioner, "_sync_groups") as mock_groups:
            await provisioner.provision()
            mock_groups.assert_not_called()

    @pytest.mark.asyncio
    async def test_lock_released_after_sync(self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock) -> None:
        mock_lock = _make_lock(acquired=True)
        mock_redis.lock.return_value = mock_lock

        with (
            patch.object(provisioner, "_sync_workspace_models"),
            patch.object(provisioner, "_sync_access_grants"),
        ):
            await provisioner.sync_agents([_RAG_AGENT])
            mock_lock.release.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lock_released_on_exception(self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock) -> None:
        mock_lock = _make_lock(acquired=True)
        mock_redis.lock.return_value = mock_lock

        with (
            patch.object(provisioner, "_sync_workspace_models", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="boom"),
        ):
            await provisioner.sync_agents([_RAG_AGENT])

        mock_lock.release.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_agent_and_access_syncs_use_separate_locks(
        self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock
    ) -> None:
        """Agent sync and access sync must not block each other."""
        lock_keys: list[str] = []
        mock_redis.lock.side_effect = lambda key, **_: (lock_keys.append(key), _make_lock(acquired=True))[1]

        with (
            patch.object(provisioner, "_sync_workspace_models"),
            patch.object(provisioner, "_sync_access_grants"),
            patch.object(provisioner, "_sync_groups"),
        ):
            await provisioner.sync_agents([_RAG_AGENT])
            await provisioner.sync_access()

        assert len(lock_keys) == 2
        assert lock_keys[0] != lock_keys[1]

    @pytest.mark.asyncio
    async def test_raises_when_not_initialized(self, provisioner: OpenWebuiProvisioner) -> None:
        OpenWebuiProvisioner._redis = None

        with pytest.raises(RuntimeError, match="not initialized"):
            await provisioner.provision()
