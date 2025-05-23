from typing import Annotated, List

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from pydantic import BaseModel, Field


class NodeSummaryDTO(BaseModel):
    level: Annotated[int, Field(..., description="Level of the summary")]
    nodes: Annotated[List[IngestedNode], Field(..., description="List of nodes in the summary")]
