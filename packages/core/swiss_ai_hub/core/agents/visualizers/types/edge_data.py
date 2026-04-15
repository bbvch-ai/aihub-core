from typing import Annotated

from pydantic import BaseModel, Field


class EdgeData(BaseModel):
    """Data for an edge in the workflow graph."""

    source: Annotated[str, Field(description="ID of the source node")]
    target: Annotated[str, Field(description="ID of the target node")]
