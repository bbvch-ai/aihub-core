from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.distributor.dependencies.use_external_agent_event_distributor import (
        use_external_agent_event_distributor,
    )
    from swiss_ai_hub.core.distributor.dependencies.use_external_process_event_distributor import (
        use_external_process_event_distributor,
    )
    from swiss_ai_hub.core.distributor.events.ExternalAgentEvent import ExternalAgentEvent
    from swiss_ai_hub.core.distributor.events.ExternalProcessEvent import ExternalProcessEvent
    from swiss_ai_hub.core.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
    from swiss_ai_hub.core.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor

__all__ = [
    "ExternalAgentEvent",
    "ExternalAgentEventDistributor",
    "ExternalProcessEvent",
    "ExternalProcessEventDistributor",
    "use_external_agent_event_distributor",
    "use_external_process_event_distributor",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ExternalAgentEvent": "swiss_ai_hub.core.distributor.events.ExternalAgentEvent",
    "ExternalAgentEventDistributor": "swiss_ai_hub.core.distributor.ExternalAgentEventDistributor",
    "ExternalProcessEvent": "swiss_ai_hub.core.distributor.events.ExternalProcessEvent",
    "ExternalProcessEventDistributor": "swiss_ai_hub.core.distributor.ExternalProcessEventDistributor",
    "use_external_agent_event_distributor": "swiss_ai_hub.core.distributor.dependencies.use_external_agent_event_distributor",
    "use_external_process_event_distributor": "swiss_ai_hub.core.distributor.dependencies.use_external_process_event_distributor",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
