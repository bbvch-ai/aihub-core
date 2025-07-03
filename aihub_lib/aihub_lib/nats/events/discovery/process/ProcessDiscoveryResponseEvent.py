from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import BaseEvent
from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after a process discovery request, detailing a process's class, ID, configuration,
    and work events that it expects to receive through API calls.

    ### Why ProcessDiscoveryResponseEvent?
    After a discovery request, consumers need to know:
    - Which process instance is available (identified by `process_class` and `process_id`).
    - What configuration that process operates under.
    - Which work events the process can receive via API.

    By providing this structured information, the discovery response helps orchestrators and clients
    dynamically integrate with newly discovered processs without manual configuration or guesswork.
    """

    process_class: Annotated[
        str, Field(description="The class or category of the process (e.g., a specific type of process).")
    ]
    process_id: Annotated[str, Field(description="A unique identifier for the process instance.")]
    process_config: Annotated[ProcessConfig, Field(description="Configuration for the process instance.")]
