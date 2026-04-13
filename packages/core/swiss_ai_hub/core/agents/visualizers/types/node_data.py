from typing import Annotated, Literal

from pydantic import BaseModel, Field


class NodeData(BaseModel):
    """Data for a node in the workflow graph."""

    id: Annotated[str, Field(description="Unique identifier for the node")]
    type: Annotated[Literal["start", "step", "stop"], Field(description="Type of node")]
    label: Annotated[str, Field(description="Display label for the node")]
    description: Annotated[str | None, Field(description="Description of the node, if available")] = None
    icon: Annotated[str | None, Field(description="Icon for the node, if available")] = None
