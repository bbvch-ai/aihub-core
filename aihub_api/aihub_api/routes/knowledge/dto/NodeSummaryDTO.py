from typing import Annotated

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from pydantic import BaseModel, Field


class NodeSummaryDTO(BaseModel):
    level: Annotated[int, Field(..., description="Level of the summary")]
    nodes: Annotated[list[IngestedNode], Field(..., description="List of nodes in the summary")]
