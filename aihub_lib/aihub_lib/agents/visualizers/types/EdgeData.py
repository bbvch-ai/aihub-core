from typing import Annotated, Dict

from pydantic import BaseModel, Field

from aihub_lib.agents.visualizers.types.EventPayloadField import EventPayloadField


class EdgeData(BaseModel):
    """Data for an edge in the workflow graph."""

    source: Annotated[str, Field(description="ID of the source node")]
    target: Annotated[str, Field(description="ID of the target node")]
    edge_id: Annotated[int, Field(description="Unique identifier for the edge")]
    event_type: Annotated[str, Field(description="Type of event represented by this edge")]
    event_full_name: Annotated[str, Field(description="Fully qualified name of the event")]
    is_start_event: Annotated[bool, Field(description="Whether this edge represents a start event")]
    is_stop_event: Annotated[bool, Field(description="Whether this edge represents a stop event")]
    payload: Annotated[Dict[str, EventPayloadField], Field(description="Payload information for the event")]
