"""Tests for per-target hash orchestration in _sync_agent_instances_to_provisioners."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from swiss_ai_hub.api.services.agent_endpoints_discovery_service import (
    AgentEndpointsDiscoveryService,
    SyncTarget,
)


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
    service._openwebui_provisioner = SimpleNamespace(model_name_locale="en")
    return service


def _make_redis(stored: dict[SyncTarget, str] | None = None) -> AsyncMock:
    """Each target owns a key, so the mock must answer per key rather than returning one value."""
    values = {AgentEndpointsDiscoveryService._agents_hash_key(t): v.encode() for t, v in (stored or {}).items()}
    redis = AsyncMock()
    redis.get.side_effect = lambda key: values.get(key)
    return redis


def _stored_keys(redis: AsyncMock) -> set[str]:
    return {call.args[0] for call in redis.set.await_args_list}


def _key(target: SyncTarget) -> str:
    return AgentEndpointsDiscoveryService._agents_hash_key(target)


_INSTANCES = [_make_instance("rag", "default"), _make_instance("chat", "main")]
_INSTANCES_HASH = AgentEndpointsDiscoveryService._compute_agents_hash(
    {(inst.agent_class, inst.agent_id, inst.name) for inst in _INSTANCES}
)


class TestSyncAgentInstancesToProvisioners:
    @pytest.mark.asyncio
    async def test_skips_sync_when_hash_unchanged(self) -> None:
        redis = _make_redis({SyncTarget.LANGFUSE: _INSTANCES_HASH, SyncTarget.OPENWEBUI: _INSTANCES_HASH})
        service = _make_service(redis=redis)

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
    async def test_resyncs_when_only_name_changed(self) -> None:
        """A rename keeps (class, id) constant but must still trigger a re-sync."""
        redis = _make_redis({SyncTarget.LANGFUSE: _INSTANCES_HASH, SyncTarget.OPENWEBUI: _INSTANCES_HASH})
        service = _make_service(redis=redis)

        renamed = [_make_instance("rag", "default"), _make_instance("chat", "main")]
        renamed[0].name = "Renamed Agent"

        with (
            patch.object(
                AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=True
            ) as mock_langfuse,
            patch.object(
                AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui", return_value=True
            ) as mock_openwebui,
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=renamed)
            await service._sync_agent_instances_to_provisioners()

            mock_langfuse.assert_awaited_once()
            mock_openwebui.assert_awaited_once()
            assert _stored_keys(redis) == {_key(SyncTarget.LANGFUSE), _key(SyncTarget.OPENWEBUI)}

    @pytest.mark.asyncio
    async def test_syncs_and_stores_both_hashes_when_changed(self) -> None:
        redis = _make_redis()
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
            assert _stored_keys(redis) == {_key(SyncTarget.LANGFUSE), _key(SyncTarget.OPENWEBUI)}
            assert redis.set.await_args_list[0].kwargs["ex"] == AgentEndpointsDiscoveryService._AGENTS_HASH_TTL

    @pytest.mark.asyncio
    async def test_stores_only_the_succeeding_target_when_langfuse_fails(self) -> None:
        redis = _make_redis()
        service = _make_service(redis=redis)

        with (
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=False),
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui", return_value=True),
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            assert _stored_keys(redis) == {_key(SyncTarget.OPENWEBUI)}

    @pytest.mark.asyncio
    async def test_stores_only_the_succeeding_target_when_openwebui_fails(self) -> None:
        redis = _make_redis()
        service = _make_service(redis=redis)

        with (
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=True),
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui", return_value=False),
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            assert _stored_keys(redis) == {_key(SyncTarget.LANGFUSE)}

    @pytest.mark.asyncio
    async def test_healthy_target_is_not_redriven_while_the_other_keeps_failing(self) -> None:
        """A permanently failing Langfuse used to re-run OpenWebUI's real HTTP writes every 60s."""
        redis = _make_redis({SyncTarget.OPENWEBUI: _INSTANCES_HASH})
        service = _make_service(redis=redis)

        with (
            patch.object(
                AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=False
            ) as mock_langfuse,
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui") as mock_openwebui,
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            mock_langfuse.assert_awaited_once()
            mock_openwebui.assert_not_awaited()
            redis.set.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_langfuse_recovers_without_redriving_openwebui(self) -> None:
        redis = _make_redis({SyncTarget.OPENWEBUI: _INSTANCES_HASH, SyncTarget.LANGFUSE: "stale"})
        service = _make_service(redis=redis)

        with (
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_langfuse", return_value=True),
            patch.object(AgentEndpointsDiscoveryService, "_sync_agent_instances_to_openwebui") as mock_openwebui,
            patch("swiss_ai_hub.api.services.agent_endpoints_discovery_service.AgentService") as mock_agent_svc,
        ):
            mock_agent_svc.get_all_agent_instances = AsyncMock(return_value=_INSTANCES)
            await service._sync_agent_instances_to_provisioners()

            mock_openwebui.assert_not_awaited()
            assert _stored_keys(redis) == {_key(SyncTarget.LANGFUSE)}
