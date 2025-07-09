from typing import Annotated

from pydantic import Field, BaseModel

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessInSpecs(BaseModel):
    route: Annotated[str, Field(description="The route of the work event.")]
    method: Annotated[str, Field(description="The HTTP method of the work event.")]
    is_process_start: Annotated[bool, Field(description="Whether the work event is a process start event.")]
    event_specs: Annotated[EventSpecs, Field(description="The event specs of the work event.")]


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
    human_inputs: Annotated[
        list[ProcessInSpecs], Field(description="List of human work events that the process can receive.")
    ]
    program_inputs: Annotated[
        list[ProcessInSpecs], Field(description="List of program work events that the process can receive.")
    ]
