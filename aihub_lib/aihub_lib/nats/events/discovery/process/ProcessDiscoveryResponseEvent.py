from pydantic import Field

from aihub_lib.nats.events import BaseEvent
from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessDiscoveryResponseEvent(BaseEvent):
    process_class: str = Field(
        ..., description="The class or category of the process (e.g., a specific type of process)."
    )
    process_id: str = Field(..., description="A unique identifier for the process instance.")
    process_config: ProcessConfig = Field(..., description="Configuration for the process instance.")
