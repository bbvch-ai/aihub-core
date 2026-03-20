from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.rpc.agent_config_responder import AgentConfigResponder
    from swiss_ai_hub.api.rpc.process_config_responder import ProcessConfigResponder

__all__ = [
    "AgentConfigResponder",
    "ProcessConfigResponder",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentConfigResponder": "swiss_ai_hub.api.rpc.agent_config_responder",
    "ProcessConfigResponder": "swiss_ai_hub.api.rpc.process_config_responder",
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
