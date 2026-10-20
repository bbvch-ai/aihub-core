"""A class going offline must not fail the discovery round when controllers are mounted through include_router."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import APIRouter, FastAPI

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
    return service


def _add_dynamic_endpoint(service: EndpointsDiscoveryService, base_path: str) -> None:
    service.app.add_api_route(f"{base_path}/start", lambda: None, methods=["POST"])


def _paths(app: FastAPI) -> set[str]:
    return {route.path for route in app.routes if hasattr(route, "path")}


class TestAgentClassGoingOffline:
    def _service(self) -> AgentEndpointsDiscoveryService:
        app = _app_with_a_mounted_controller("/agents")
        service = _make_service(AgentEndpointsDiscoveryService, app, "/agents", {"Gone", "Alive"})
        for agent_class in ("Gone", "Alive"):
            _add_dynamic_endpoint(service, service._get_endpoint_base_path_for_class(agent_class))
        service._sync_agent_instances_to_provisioners = AsyncMock()
        service._sync_knowledge_to_openwebui = AsyncMock()
        service._register_class_endpoints = MagicMock()
        return service

    def test_only_the_offline_class_loses_its_endpoints(self) -> None:
        service = self._service()

        service._deregister_endpoints_for_class("Gone")

        assert "/agents/classes/Gone/instances/{agent_id}/start" not in _paths(service.app)
        assert "/agents/classes/Alive/instances/{agent_id}/start" in _paths(service.app)
        assert service.registered_classes == {"Alive"}

    @pytest.mark.asyncio
    async def test_the_round_still_registers_new_classes_and_syncs(self) -> None:
        service = self._service()
        service._broadcast_discovery = AsyncMock(
            return_value=[
                SimpleNamespace(
                    agent_class=name,
                    start_events=[],
                    stop_events=[],
                    hitl_request_events=[],
                    hitl_response_events=[],
                )
                for name in ("Alive", "Fresh")
            ]
        )

        await service._discover_and_register()

        assert service.registered_classes == {"Alive", "Fresh"}
        assert service._register_class_endpoints.call_args.kwargs["agent_class"] == "Fresh"
        service._sync_agent_instances_to_provisioners.assert_awaited_once()
        service._sync_knowledge_to_openwebui.assert_awaited_once()


class TestProcessClassGoingOffline:
    @pytest.mark.asyncio
    async def test_the_round_removes_its_endpoints_and_registers_new_classes(self) -> None:
        app = _app_with_a_mounted_controller("/processes")
        service = _make_service(ProcessEndpointsDiscoveryService, app, "/processes", {"Gone"})
        _add_dynamic_endpoint(service, service._get_endpoint_base_path_for_process_class("Gone"))
        service._broadcast_discovery = AsyncMock(return_value=[SimpleNamespace(process_class="Fresh")])
        service._register_class_endpoints = MagicMock()

        await service._discover_and_register()

        assert "/processes/classes/Gone/instances/{process_id}/start" not in _paths(app)
        assert service.registered_classes == {"Fresh"}
        service._register_class_endpoints.assert_called_once()
