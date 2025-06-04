from pydantic import Field

from aihub_lib.nats.events import BaseEvent


class ProcessDiscoveryResponseEvent(BaseEvent):
    process_class: str = Field(
        ..., description="The class or category of the process (e.g., a specific type of process)."
    )
    process_id: str = Field(..., description="A unique identifier for the process instance.")
