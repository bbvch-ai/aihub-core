"""Tests for hash-based sync orchestration in _sync_agent_instances_to_provisioners."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from swiss_ai_hub.api.services.agent_endpoints_discovery_service import AgentEndpointsDiscoveryService


def _make_instance(agent_class: str, agent_id: str, *, is_conversational: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        agent_class=agent_class,
        agent_id=agent_id,
        name=f"{agent_class}/{agent_id}",
        is_conversational=is_conversational,
    )


def _make_service(*, redis: AsyncMock) -> AgentEndpointsDiscoveryService:
    service = object.__new__(AgentEndpointsDiscoveryService)
    service._redis = redis
    service.locale_handler = AsyncMock()
    return service


_INSTANCES = [_make_instance("rag", "default"), _make_instance("chat", "main")]


class TestSyncAgentInstancesToProvisioners:
    @pytest.mark.asyncio
    async def test_skips_sync_when_hash_unchanged(self) -> None:
        redis = AsyncMock()
        service = _make_service(redis=redis)

        expected_hash = service._compute_agents_hash({(inst.agent_class, inst.agent_id) for inst in _INSTANCES})
        redis.get.return_value = expected_hash.encode()

        with (
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse") as mock_langfuse,
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui") as mock_openwebui,
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            mock_langfuse.assert_not_called()
            mock_openwebui.assert_not_called()

    @pytest.mark.asyncio
    async def test_syncs_and_stores_hash_when_changed(self) -> None:
        redis = AsyncMock()
        redis.get.return_value = None
        service = _make_service(redis=redis)

        with (
            patch.object(
                AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=True
            ) as mock_langfuse,
            patch.object(
                AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui", return_value=True
            ) as mock_openwebui,
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            mock_langfuse.assert_awaited_once()
            mock_openwebui.assert_awaited_once()
            redis.set.assert_awaited_once()
            assert redis.set.call_args[1]["ex"] == AgentEndpointsDiscoveryService._AGENTS_HASH_TTL

    @pytest.mark.asyncio
    async def test_does_not_store_hash_when_langfuse_fails(self) -> None:
        redis = AsyncMock()
        redis.get.return_value = None
        service = _make_service(redis=redis)

        with (
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=False),
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui", return_value=True),
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            redis.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_does_not_store_hash_when_openwebui_fails(self) -> None:
        redis = AsyncMock()
        redis.get.return_value = None
        service = _make_service(redis=redis)

        with (
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=True),
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui", return_value=False),
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            redis.set.assert_not_awaited()
