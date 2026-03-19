from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.runners.agent_runner import AgentRunner
    from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner, ObservedEvent
    from swiss_ai_hub.agent.runners.multiprocess_agent_runner import MultiprocessAgentRunner

__all__ = [
    "AgentRunner",
    "AgentTestRunner",
    "MultiprocessAgentRunner",
    "ObservedEvent",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentRunner": "swiss_ai_hub.agent.runners.agent_runner",
    "AgentTestRunner": "swiss_ai_hub.agent.runners.agent_test_runner",
    "MultiprocessAgentRunner": "swiss_ai_hub.agent.runners.multiprocess_agent_runner",
    "ObservedEvent": "swiss_ai_hub.agent.runners.agent_test_runner",
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
