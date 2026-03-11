from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.agents import EdgeData
from swiss_ai_hub.core.agents import NodeData


class MemoryGraphResponse(BaseModel):
    """Response in sigma.js compatible graph format for knowledge graph visualization."""

    directed: Annotated[bool, Field(description="Graph is directed (edges have direction).")] = True
    multigraph: Annotated[bool, Field(description="Allows multiple edges between the same nodes.")] = True
    graph: Annotated[dict[str, Any], Field(description="Graph-level metadata.")] = {}
    nodes: Annotated[list[NodeData], Field(description="List of nodes in the graph (entities).")]
    links: Annotated[list[EdgeData], Field(description="List of edges in the graph (relations).")]
