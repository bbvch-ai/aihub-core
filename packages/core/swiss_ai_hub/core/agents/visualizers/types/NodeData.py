from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.agents.visualizers.types.EventInfo import EventInfo
from swiss_ai_hub.core.agents.visualizers.types.InputEventInfo import InputEventInfo


class NodeData(BaseModel):
    """Data for a node in the workflow graph."""

    id: Annotated[str, Field(description="Unique identifier for the node")]
    type: Annotated[str, Field(description="Type of node (step, start, stop)")]
    node_id: Annotated[str, Field(description="Internal identifier for the node")]
    label: Annotated[str, Field(description="Display label for the node")]
    description: Annotated[str | None, Field(description="Description of the node, if available")] = None
    icon: Annotated[str | None, Field(description="Icon for the node, if available")] = None
    input_events: Annotated[
        dict[str, InputEventInfo] | None, Field(description="Input events required by this node")
    ] = None
    output_events: Annotated[list[EventInfo] | None, Field(description="Output events produced by this node")] = None
    max_executions: Annotated[int | None, Field(description="Maximum number of times this node can be executed")] = None
    stop_on_error: Annotated[bool | None, Field(description="Whether workflow should stop on error in this node")] = (
        None
    )
