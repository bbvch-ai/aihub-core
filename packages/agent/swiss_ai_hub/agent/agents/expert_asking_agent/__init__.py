from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent import ExpertAskingAgent
    from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent_config import ExpertAskingAgentConfig

__all__ = ["ExpertAskingAgent", "ExpertAskingAgentConfig"]

_LAZY_IMPORTS: dict[str, str] = {
    "ExpertAskingAgent": "swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent",
    "ExpertAskingAgentConfig": "swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent_config",
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
