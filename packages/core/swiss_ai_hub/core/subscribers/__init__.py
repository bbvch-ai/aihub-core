from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.subscribers.abstract_subscriber import AbstractSubscriber
    from swiss_ai_hub.core.subscribers.agent.agent_js_subscriber import AgentJSSubscriber
    from swiss_ai_hub.core.subscribers.agent.agent_nc_subscriber import AgentNCSubscriber
    from swiss_ai_hub.core.subscribers.js_subscriber import JSSubscriber
    from swiss_ai_hub.core.subscribers.nc_subscriber import NCSubscriber
    from swiss_ai_hub.core.subscribers.process.process_js_subscriber import ProcessJSSubscriber
    from swiss_ai_hub.core.subscribers.process.process_nc_subscriber import ProcessNCSubscriber

__all__ = [
    "AbstractSubscriber",
    "AgentJSSubscriber",
    "AgentNCSubscriber",
    "JSSubscriber",
    "NCSubscriber",
    "ProcessJSSubscriber",
    "ProcessNCSubscriber",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AbstractSubscriber": "swiss_ai_hub.core.subscribers.abstract_subscriber",
    "AgentJSSubscriber": "swiss_ai_hub.core.subscribers.agent.agent_js_subscriber",
    "AgentNCSubscriber": "swiss_ai_hub.core.subscribers.agent.agent_nc_subscriber",
    "JSSubscriber": "swiss_ai_hub.core.subscribers.js_subscriber",
    "NCSubscriber": "swiss_ai_hub.core.subscribers.nc_subscriber",
    "ProcessJSSubscriber": "swiss_ai_hub.core.subscribers.process.process_js_subscriber",
    "ProcessNCSubscriber": "swiss_ai_hub.core.subscribers.process.process_nc_subscriber",
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
