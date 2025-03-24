from typing import Annotated, List, Dict, Any

from pydantic import BaseModel, Field

from aihub_lib.agents.visualizers.types.EdgeData import EdgeData
from aihub_lib.agents.visualizers.types.NodeData import NodeData


class WorkflowGraph(BaseModel):
    """Complete workflow graph representation."""
    directed: Annotated[bool, Field(description="Whether the graph is directed")]
    multigraph: Annotated[bool, Field(description="Whether the graph is a multigraph")]
    graph: Annotated[Dict[str, Any], Field(description="Graph-level attributes")]
    nodes: Annotated[List[NodeData], Field(description="List of nodes in the graph")]
    links: Annotated[List[EdgeData], Field(description="List of edges in the graph")]
