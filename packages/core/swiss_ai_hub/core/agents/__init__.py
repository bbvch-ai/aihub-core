from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.agents.AgentConfig import AgentConfig, StepConfig
    from swiss_ai_hub.core.agents.AgentRef import AgentRef
    from swiss_ai_hub.core.agents.visualizers.types.EdgeData import EdgeData
    from swiss_ai_hub.core.agents.visualizers.types.NodeData import NodeData
    from swiss_ai_hub.core.agents.visualizers.types.WorkflowGraph import WorkflowGraph

__all__ = [
    "AgentConfig",
    "AgentRef",
    "EdgeData",
    "NodeData",
    "StepConfig",
    "WorkflowGraph",
]

_LAZY_IMPORTS = {
    "AgentConfig": "swiss_ai_hub.core.agents.AgentConfig",
    "AgentRef": "swiss_ai_hub.core.agents.AgentRef",
    "EdgeData": "swiss_ai_hub.core.agents.visualizers.types.EdgeData",
    "NodeData": "swiss_ai_hub.core.agents.visualizers.types.NodeData",
    "StepConfig": "swiss_ai_hub.core.agents.AgentConfig",
    "WorkflowGraph": "swiss_ai_hub.core.agents.visualizers.types.WorkflowGraph",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
