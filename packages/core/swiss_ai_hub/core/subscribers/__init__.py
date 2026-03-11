from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.subscribers.AbstractSubscriber import AbstractSubscriber
    from swiss_ai_hub.core.subscribers.agent.AgentJSSubscriber import AgentJSSubscriber
    from swiss_ai_hub.core.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
    from swiss_ai_hub.core.subscribers.JSSubscriber import JSSubscriber
    from swiss_ai_hub.core.subscribers.NCSubscriber import NCSubscriber
    from swiss_ai_hub.core.subscribers.process.ProcessJSSubscriber import ProcessJSSubscriber
    from swiss_ai_hub.core.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber

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
    "AbstractSubscriber": "swiss_ai_hub.core.subscribers.AbstractSubscriber",
    "AgentJSSubscriber": "swiss_ai_hub.core.subscribers.agent.AgentJSSubscriber",
    "AgentNCSubscriber": "swiss_ai_hub.core.subscribers.agent.AgentNCSubscriber",
    "JSSubscriber": "swiss_ai_hub.core.subscribers.JSSubscriber",
    "NCSubscriber": "swiss_ai_hub.core.subscribers.NCSubscriber",
    "ProcessJSSubscriber": "swiss_ai_hub.core.subscribers.process.ProcessJSSubscriber",
    "ProcessNCSubscriber": "swiss_ai_hub.core.subscribers.process.ProcessNCSubscriber",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
