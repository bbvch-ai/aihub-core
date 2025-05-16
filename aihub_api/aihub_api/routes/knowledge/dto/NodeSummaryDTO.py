from typing import Annotated, List

from pydantic import BaseModel, Field

from aihub_api.routes.knowledge.dto.NodeDTO import NodeDTO


class NodeSummaryDTO(BaseModel):
    level: Annotated[int, Field(..., description="Level of the summary")]
    nodes: Annotated[List[NodeDTO], Field(..., description="List of nodes in the summary")]