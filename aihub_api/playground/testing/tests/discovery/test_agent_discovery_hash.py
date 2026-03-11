"""Tests for AgentEndpointsDiscoveryService Redis-based agent hash check."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from aihub_api.services.AgentEndpointsDiscoveryService import AgentEndpointsDiscoveryService


@pytest.fixture
def mock_redis() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_redis: MagicMock) -> MagicMock:
    svc = MagicMock(spec=AgentEndpointsDiscoveryService)
    svc._redis = mock_redis
    return svc


class TestAgentHashCheck:
    def test_compute_agents_hash_deterministic(self) -> None:
        set_a = {("rag", "default"), ("chat", "main")}
        set_b = {("chat", "main"), ("rag", "default")}
        assert AgentEndpointsDiscoveryService._compute_agents_hash(
            set_a
        ) == AgentEndpointsDiscoveryService._compute_agents_hash(set_b)

    def test_compute_agents_hash_differs_for_different_sets(self) -> None:
        set_a = {("rag", "default")}
        set_b = {("chat", "main")}
        assert AgentEndpointsDiscoveryService._compute_agents_hash(
            set_a
        ) != AgentEndpointsDiscoveryService._compute_agents_hash(set_b)

    @pytest.mark.asyncio
    async def test_hash_unchanged_returns_true_when_redis_has_same_hash(
        self, service: MagicMock, mock_redis: MagicMock
    ) -> None:
        mock_redis.get = AsyncMock(return_value=b"abc123")

        result = await AgentEndpointsDiscoveryService._agents_hash_unchanged(service, "abc123")
        assert result is True

    @pytest.mark.asyncio
    async def test_hash_unchanged_returns_false_when_redis_has_different_hash(
        self, service: MagicMock, mock_redis: MagicMock
    ) -> None:
        mock_redis.get = AsyncMock(return_value=b"old_hash")

        result = await AgentEndpointsDiscoveryService._agents_hash_unchanged(service, "new_hash")
        assert result is False

    @pytest.mark.asyncio
    async def test_hash_unchanged_returns_false_when_no_stored_hash(
        self, service: MagicMock, mock_redis: MagicMock
    ) -> None:
        mock_redis.get = AsyncMock(return_value=None)

        result = await AgentEndpointsDiscoveryService._agents_hash_unchanged(service, "any_hash")
        assert result is False

    @pytest.mark.asyncio
    async def test_store_agents_hash_sets_with_ttl(self, service: MagicMock, mock_redis: MagicMock) -> None:
        mock_redis.set = AsyncMock()

        await AgentEndpointsDiscoveryService._store_agents_hash(service, "abc123")
        mock_redis.set.assert_awaited_once_with("openwebui:agents:hash", "abc123", ex=3600)
