from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.agents.visualizers.types.edge_data import EdgeData
from swiss_ai_hub.core.agents.visualizers.types.node_data import NodeData


class WorkflowGraph(BaseModel):
    """Complete workflow graph representation."""

    nodes: Annotated[list[NodeData], Field(description="List of nodes in the graph")]
    links: Annotated[list[EdgeData], Field(description="List of edges in the graph")]
