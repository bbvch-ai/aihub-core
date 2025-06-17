from pydantic import Field

from aihub_lib.nats.events import BaseEvent
from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after an process discovery request, detailing an process's class, ID, configuration,
    and work events that it expects to receive through API calls.

    ### Why ProcessDiscoveryResponseEvent?
    After a discovery request, consumers need to know:
    - Which process instance is available (identified by `process_class` and `process_id`).
    - What configuration that process operates under.
    - Which work events the process can receive via API.

    By providing this structured information, the discovery response helps orchestrators and clients
    dynamically integrate with newly discovered processs without manual configuration or guesswork.
    """

    process_class: str = Field(
        ..., description="The class or category of the process (e.g., a specific type of process)."
    )
    process_id: str = Field(..., description="A unique identifier for the process instance.")
    process_config: ProcessConfig = Field(..., description="Configuration for the process instance.")
