from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.distributor.dependencies.use_external_agent_event_distributor import (
        use_external_agent_event_distributor,
    )
    from swiss_ai_hub.core.distributor.dependencies.use_external_process_event_distributor import (
        use_external_process_event_distributor,
    )
    from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
    from swiss_ai_hub.core.distributor.events.external_process_event import ExternalProcessEvent
    from swiss_ai_hub.core.distributor.external_agent_event_distributor import ExternalAgentEventDistributor
    from swiss_ai_hub.core.distributor.external_process_event_distributor import ExternalProcessEventDistributor

__all__ = [
    "ExternalAgentEvent",
    "ExternalAgentEventDistributor",
    "ExternalProcessEvent",
    "ExternalProcessEventDistributor",
    "use_external_agent_event_distributor",
    "use_external_process_event_distributor",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ExternalAgentEvent": "swiss_ai_hub.core.distributor.events.external_agent_event",
    "ExternalAgentEventDistributor": "swiss_ai_hub.core.distributor.external_agent_event_distributor",
    "ExternalProcessEvent": "swiss_ai_hub.core.distributor.events.external_process_event",
    "ExternalProcessEventDistributor": "swiss_ai_hub.core.distributor.external_process_event_distributor",
    "use_external_agent_event_distributor": "swiss_ai_hub.core.distributor.dependencies.use_external_agent_event_distributor",
    "use_external_process_event_distributor": "swiss_ai_hub.core.distributor.dependencies.use_external_process_event_distributor",
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
