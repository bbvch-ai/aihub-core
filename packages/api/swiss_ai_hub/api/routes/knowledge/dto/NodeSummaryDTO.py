from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode


class NodeSummaryDTO(BaseModel):
    level: Annotated[int, Field(..., description="Level of the summary")]
    nodes: Annotated[list[IngestedNode], Field(..., description="List of nodes in the summary")]
