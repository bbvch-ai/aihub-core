from typing import Annotated, List

from aihub_lib.nats.events.semantic.retriever.Node import Node
from pydantic import BaseModel, Field


class NodeSummaryDTO(BaseModel):
    level: Annotated[int, Field(..., description="Level of the summary")]
    nodes: Annotated[List[Node], Field(..., description="List of nodes in the summary")]
