from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.process.delegators.abstract_entity_delegator import AbstractEntityDelegator
    from swiss_ai_hub.process.delegators.abstract_process_entity import BaseProcessEntity
    from swiss_ai_hub.process.delegators.agent.agent import Agent
    from swiss_ai_hub.process.delegators.agent.agent_delegator import AgentDelegator
    from swiss_ai_hub.process.delegators.human.human import Human
    from swiss_ai_hub.process.delegators.process.process import Process
    from swiss_ai_hub.process.delegators.process.process_delegator import ProcessDelegator
    from swiss_ai_hub.process.delegators.program.program import Program

__all__ = [
    "AbstractEntityDelegator",
    "Agent",
    "AgentDelegator",
    "BaseProcessEntity",
    "Human",
    "Process",
    "ProcessDelegator",
    "Program",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AbstractEntityDelegator": "swiss_ai_hub.process.delegators.abstract_entity_delegator",
    "Agent": "swiss_ai_hub.process.delegators.agent.agent",
    "AgentDelegator": "swiss_ai_hub.process.delegators.agent.agent_delegator",
    "BaseProcessEntity": "swiss_ai_hub.process.delegators.abstract_process_entity",
    "Human": "swiss_ai_hub.process.delegators.human.human",
    "Process": "swiss_ai_hub.process.delegators.process.process",
    "ProcessDelegator": "swiss_ai_hub.process.delegators.process.process_delegator",
    "Program": "swiss_ai_hub.process.delegators.program.program",
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
