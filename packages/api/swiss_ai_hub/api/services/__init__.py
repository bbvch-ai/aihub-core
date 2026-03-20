from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.services.agent_endpoints_discovery_service import AgentEndpointsDiscoveryService
    from swiss_ai_hub.api.services.model_creation_service import ModelCreationService
    from swiss_ai_hub.api.services.process_endpoints_discovery_service import ProcessEndpointsDiscoveryService

__all__ = [
    "AgentEndpointsDiscoveryService",
    "ModelCreationService",
    "ProcessEndpointsDiscoveryService",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentEndpointsDiscoveryService": "swiss_ai_hub.api.services.agent_endpoints_discovery_service",
    "ModelCreationService": "swiss_ai_hub.api.services.model_creation_service",
    "ProcessEndpointsDiscoveryService": "swiss_ai_hub.api.services.process_endpoints_discovery_service",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
