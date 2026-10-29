"""A class loses its endpoints only after missing the configured completed rounds, and a broken round changes nothing.

Online status counts completed discovery rounds (#1970). A round that raises, stalls or runs while NATS is
reconnecting is not recorded, so it must neither remove endpoints nor feed the missed-rounds count.
"""

import asyncio
import logging
from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import APIRouter, FastAPI
from swiss_ai_hub.core.discovery import DiscoverySettings
from swiss_ai_hub.core.persistence import DiscoveryRoundEntity

from swiss_ai_hub.api.services.agent_endpoints_discovery_service import AgentEndpointsDiscoveryService
from swiss_ai_hub.api.services.endpoints_discovery_service import EndpointsDiscoveryService
from swiss_ai_hub.api.services.process_endpoints_discovery_service import ProcessEndpointsDiscoveryService


def _app_with_a_mounted_controller(base_route: str) -> FastAPI:
    """Mounted the way `Controller.mount` does it, which since FastAPI 0.14x leaves an `_IncludedRouter` in routes."""
    app = FastAPI()
    controller_router = APIRouter()
    controller_router.add_api_route("/classes", lambda: [], methods=["GET"])
    app.include_router(controller_router, prefix=base_route)
    return app


def _make_service[TService: EndpointsDiscoveryService](
    service_class: type[TService], app: FastAPI, base_route: str, registered: set[str]
) -> TService:
    service = object.__new__(service_class)
    service.app = app
    service.controller = SimpleNamespace(base_route=base_route)
    service.registered_classes = set(registered)
    service.registered_entities = set()
    service.nc = SimpleNamespace(is_connected=True)
    service.settings = DiscoverySettings()
    return service


def _add_dynamic_endpoint(service: EndpointsDiscoveryService, base_path: str) -> None:
    service.app.add_api_route(f"{base_path}/start", lambda: None, methods=["POST"])


def _paths(app: FastAPI) -> set[str]:
    return {route.path for route in app.routes if hasattr(route, "path")}


def _agent_answer(agent_class: str) -> SimpleNamespace:
    return SimpleNamespace(
        agent_class=agent_class, start_events=[], stop_events=[], hitl_request_events=[], hitl_response_events=[]
    )


@pytest.fixture(autouse=True)
def recorded_rounds() -> Iterator[MagicMock]:
    with patch.object(DiscoveryRoundEntity, "record_completed") as record_completed:
        yield record_completed


class TestAgentClassGoingOffline:
    def _service(self, online_by_rule: set[str]) -> AgentEndpointsDiscoveryService:
        app = _app_with_a_mounted_controller("/agents")
        service = _make_service(AgentEndpointsDiscoveryService, app, "/agents", {"Gone", "Alive"})
        for agent_class in ("Gone", "Alive"):
            _add_dynamic_endpoint(service, service._get_endpoint_base_path_for_class(agent_class))
        service._sync_agent_instances_to_provisioners = AsyncMock()
        service._sync_knowledge_to_openwebui = AsyncMock()
        service._register_class_endpoints = MagicMock()
        service._online_class_names = MagicMock(return_value=online_by_rule)
        return service

    def test_only_the_offline_class_loses_its_endpoints(self) -> None:
        service = self._service(online_by_rule=set())

        service._deregister_endpoints_for_class("Gone")

        assert "/agents/classes/Gone/instances/{agent_id}/start" not in _paths(service.app)
        assert "/agents/classes/Alive/instances/{agent_id}/start" in _paths(service.app)
        assert service.registered_classes == {"Alive"}

    @pytest.mark.asyncio
    async def test_a_class_that_missed_one_round_keeps_its_endpoints(self) -> None:
        """Before #1970 one missed round removed the endpoints while `is_online` still said online."""
        service = self._service(online_by_rule={"Gone", "Alive"})
        service._broadcast_discovery = AsyncMock(return_value=[_agent_answer("Alive")])

        assert await service._discover_and_register() is True

        assert "/agents/classes/Gone/instances/{agent_id}/start" in _paths(service.app)
        assert service.registered_classes == {"Gone", "Alive"}

    @pytest.mark.asyncio
    async def test_a_class_past_the_missed_rounds_loses_its_endpoints(self) -> None:
        service = self._service(online_by_rule={"Alive"})
        service._broadcast_discovery = AsyncMock(return_value=[_agent_answer("Alive")])

        await service._discover_and_register()

        assert "/agents/classes/Gone/instances/{agent_id}/start" not in _paths(service.app)
        assert service.registered_classes == {"Alive"}

    @pytest.mark.asyncio
    async def test_the_round_registers_new_classes_records_itself_and_syncs(self, recorded_rounds: MagicMock) -> None:
        service = self._service(online_by_rule={"Alive"})
        service._broadcast_discovery = AsyncMock(return_value=[_agent_answer("Alive"), _agent_answer("Fresh")])

        assert await service._run_round() is True
        await service._run_after_round()

        assert service.registered_classes == {"Alive", "Fresh"}
        assert service._register_class_endpoints.call_args.kwargs["agent_class"] == "Fresh"
        recorded_rounds.assert_called_once()
        service._sync_agent_instances_to_provisioners.assert_awaited_once()
        service._sync_knowledge_to_openwebui.assert_awaited_once()


class TestARoundThatDoesNotComplete:
    def _service(self) -> AgentEndpointsDiscoveryService:
        service = _make_service(
            AgentEndpointsDiscoveryService, _app_with_a_mounted_controller("/agents"), "/agents", {"Alive"}
        )
        _add_dynamic_endpoint(service, service._get_endpoint_base_path_for_class("Alive"))
        service._online_class_names = MagicMock(return_value=set())
        return service

    def _assert_nothing_changed(self, service: AgentEndpointsDiscoveryService, recorded_rounds: MagicMock) -> None:
        recorded_rounds.assert_not_called()
        assert service.registered_classes == {"Alive"}
        assert "/agents/classes/Alive/instances/{agent_id}/start" in _paths(service.app)

    @pytest.mark.asyncio
    async def test_a_round_that_raises_is_logged_and_not_counted(
        self, recorded_rounds: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        service = self._service()
        service._broadcast_discovery = AsyncMock(side_effect=RuntimeError("event loop starved"))

        with caplog.at_level(logging.ERROR):
            assert await service._run_round() is False

        assert "discovery round failed" in caplog.text
        self._assert_nothing_changed(service, recorded_rounds)

    @pytest.mark.asyncio
    async def test_a_stalled_round_is_abandoned_logged_and_not_counted(
        self, recorded_rounds: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Before #1970 a round that never returned logged nothing at all."""
        service = self._service()
        service.settings = DiscoverySettings.model_construct(ROUND_TIMEOUT_SECONDS=0.05)

        async def never_answers() -> list:
            await asyncio.sleep(10)
            return []

        service._broadcast_discovery = never_answers

        with caplog.at_level(logging.ERROR):
            assert await service._run_round() is False

        assert "stalled" in caplog.text
        self._assert_nothing_changed(service, recorded_rounds)

    @pytest.mark.asyncio
    async def test_a_round_while_nats_reconnects_is_not_counted(
        self, recorded_rounds: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """nats-py buffers the request instead of raising, so the round would otherwise see zero answers."""
        service = self._service()

        async def disconnects_during_the_wait() -> list:
            service.nc.is_connected = False
            return []

        service._broadcast_discovery = disconnects_during_the_wait

        with caplog.at_level(logging.ERROR):
            assert await service._run_round() is False

        assert "NATS was not connected while collecting answers" in caplog.text
        self._assert_nothing_changed(service, recorded_rounds)

    @pytest.mark.asyncio
    async def test_no_request_is_broadcast_while_nats_is_down(self, recorded_rounds: MagicMock) -> None:
        service = self._service()
        service.nc.is_connected = False
        service._broadcast_discovery = AsyncMock()

        assert await service._run_round() is False

        service._broadcast_discovery.assert_not_awaited()
        self._assert_nothing_changed(service, recorded_rounds)

    @pytest.mark.asyncio
    async def test_a_failing_sync_after_the_round_does_not_stop_the_loop(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        service = self._service()
        service._sync_agent_instances_to_provisioners = AsyncMock(side_effect=RuntimeError("OpenWebUI down"))

        with caplog.at_level(logging.ERROR):
            await service._run_after_round()

        assert "OpenWebUI down" in caplog.text


class TestProcessClassGoingOffline:
    def _service(self, online_by_rule: set[str]) -> ProcessEndpointsDiscoveryService:
        app = _app_with_a_mounted_controller("/processes")
        service = _make_service(ProcessEndpointsDiscoveryService, app, "/processes", {"Gone"})
        _add_dynamic_endpoint(service, service._get_endpoint_base_path_for_process_class("Gone"))
        service._register_class_endpoints = MagicMock()
        service._online_class_names = MagicMock(return_value=online_by_rule)
        service._broadcast_discovery = AsyncMock(return_value=[SimpleNamespace(process_class="Fresh")])
        return service

    @pytest.mark.asyncio
    async def test_a_class_that_missed_one_round_keeps_its_endpoints(self) -> None:
        service = self._service(online_by_rule={"Gone"})

        await service._discover_and_register()

        assert "/processes/classes/Gone/instances/{process_id}/start" in _paths(service.app)
        assert service.registered_classes == {"Gone", "Fresh"}

    @pytest.mark.asyncio
    async def test_a_class_past_the_missed_rounds_loses_its_endpoints(self) -> None:
        service = self._service(online_by_rule=set())

        await service._discover_and_register()

        assert "/processes/classes/Gone/instances/{process_id}/start" not in _paths(service.app)
        assert service.registered_classes == {"Fresh"}
        service._register_class_endpoints.assert_called_once()
