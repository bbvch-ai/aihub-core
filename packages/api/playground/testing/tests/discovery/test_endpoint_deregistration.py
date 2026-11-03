from unittest.mock import Mock

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from swiss_ai_hub.core.discovery import DiscoveryKind
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import Controller
from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

from swiss_ai_hub.api.services.endpoints_discovery_service import EndpointsDiscoveryService
from swiss_ai_hub.api.services.process_endpoints_discovery_service import ProcessEndpointsDiscoveryService


class DiscoveryServiceForTests(EndpointsDiscoveryService[BaseModel]):
    discovery_kind = DiscoveryKind.AGENT

    async def _broadcast_discovery(self) -> list[BaseModel]:
        return []

    def _class_name_of(self, dto: BaseModel) -> str:
        return ""

    def _register_discovered_class(self, dto: BaseModel) -> None:
        pass

    def _online_class_names(self) -> set[str]:
        return set()


@pytest.mark.parametrize("tenant_scoped", [False, True])
@pytest.mark.parametrize("kind", ["instance", "legacy-instance", "agent-class", "process-class"])
def test_deregistration_removes_only_matching_dynamic_endpoints(kind: str, tenant_scoped: bool):
    app = FastAPI()
    static_router = APIRouter()

    @static_router.get("/settings")
    def settings():
        return {"static": True}

    app.include_router(static_router)
    controller_type = TenantScopedController if tenant_scoped else Controller
    controller = controller_type(auth=Mock(), route="/process" if kind == "process-class" else "/agent")
    service_type = ProcessEndpointsDiscoveryService if kind == "process-class" else DiscoveryServiceForTests
    service = service_type(nc=Mock(), api_app=app, controller=controller, locale_handler=LocaleHandler(), redis=Mock())

    if kind in {"instance", "legacy-instance"}:
        base_path = service._get_endpoint_base_path_for_instance("Example", "one")
        neighbour_base_path = service._get_endpoint_base_path_for_instance("Example", "one-more")
        service.registered_entities.update({("Example", "one"), ("Example", "one-more")})
    elif kind == "process-class":
        base_path = service._get_endpoint_base_path_for_process_class("Example")
        neighbour_base_path = service._get_endpoint_base_path_for_process_class("ExampleMore")
        service.registered_classes.update({"Example", "ExampleMore"})
    else:
        base_path = service._get_endpoint_base_path_for_class("Example")
        neighbour_base_path = service._get_endpoint_base_path_for_class("ExampleMore")
        service.registered_classes.update({"Example", "ExampleMore"})

    def result():
        return {"version": "original"}

    def replacement():
        return {"version": "replacement"}

    target_paths = [f"{base_path}/Start", f"{base_path}/Start/stream"]
    neighbour_path = f"{neighbour_base_path}/Start"
    for path in [*target_paths, neighbour_path]:
        app.add_api_route(path, result, methods=["POST"])

    def url(path: str) -> str:
        return path.replace("{tenant_id}", "tenant-a").replace("{agent_id}", "one").replace("{process_id}", "one")

    def deregister():
        if kind == "instance":
            service._deregister_endpoints_for_instance("Example", "one")
        elif kind == "legacy-instance":
            service._deregister_endpoints("Example", "one")
        else:
            service._deregister_endpoints_for_class("Example")

    with TestClient(app) as client:
        # Warm the included-router/request caches and OpenAPI before changing routes.
        assert client.get("/settings").json() == {"static": True}
        for path in target_paths:
            assert client.post(url(path)).json() == {"version": "original"}
            assert path in app.openapi()["paths"]

        deregister()

        for path in target_paths:
            assert client.post(url(path)).status_code == 404
            assert path not in app.openapi()["paths"]
        assert client.post(url(neighbour_path)).json() == {"version": "original"}
        assert neighbour_path in app.openapi()["paths"]
        assert client.get("/settings").json() == {"static": True}
        if kind in {"instance", "legacy-instance"}:
            assert service.registered_entities == {("Example", "one-more")}
        else:
            assert service.registered_classes == {"ExampleMore"}

        # Repeated removal must be harmless, and a re-discovered endpoint must work.
        deregister()
        app.add_api_route(target_paths[0], replacement, methods=["POST"])
        assert client.post(url(target_paths[0])).json() == {"version": "replacement"}
