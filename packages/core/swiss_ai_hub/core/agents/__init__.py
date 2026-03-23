from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.agents.agent_config import AgentConfig, StepConfig
    from swiss_ai_hub.core.agents.agent_ref import AgentRef
    from swiss_ai_hub.core.agents.visualizers.types.edge_data import EdgeData
    from swiss_ai_hub.core.agents.visualizers.types.node_data import NodeData
    from swiss_ai_hub.core.agents.visualizers.types.workflow_graph import WorkflowGraph

__all__ = [
    "AgentConfig",
    "AgentRef",
    "EdgeData",
    "NodeData",
    "StepConfig",
    "WorkflowGraph",
]

_LAZY_IMPORTS = {
    "AgentConfig": "swiss_ai_hub.core.agents.agent_config",
    "AgentRef": "swiss_ai_hub.core.agents.agent_ref",
    "EdgeData": "swiss_ai_hub.core.agents.visualizers.types.edge_data",
    "NodeData": "swiss_ai_hub.core.agents.visualizers.types.node_data",
    "StepConfig": "swiss_ai_hub.core.agents.agent_config",
    "WorkflowGraph": "swiss_ai_hub.core.agents.visualizers.types.workflow_graph",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
