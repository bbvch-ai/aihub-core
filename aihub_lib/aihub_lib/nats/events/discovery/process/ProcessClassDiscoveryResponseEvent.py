from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.process.ProcessConfigSpecs import ProcessConfigSpecs
from aihub_lib.nats.events.discovery.process.agent_in.AgentInSpecs import AgentInSpecs
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.discovery.process.program_in.ProgramInSpecs import ProgramInSpecs
from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessClassDiscoveryResponseEvent(BaseEvent):
    """
    A response event sent after a process discovery request, detailing a process's class, ID, configuration,
    and work events that it expects to receive through API calls.

    ### Why ProcessDiscoveryResponseEvent?
    After a discovery request, consumers need to know:
    - Which process instance is available (identified by `process_class` and `process_id`).
    - What configuration that process operates under.
    - Which human / program & agent work events the process can receive via API

    By providing this structured information, the discovery response helps orchestrators and clients
    dynamically integrate with newly discovered processes without manual configuration or guesswork.
    """

    process_class: Annotated[
        str, Field(description="The class or category of the process (e.g., a specific type of process).")
    ]
    process_config_specs: Annotated[
        ProcessConfigSpecs,
        Field(
            description="A specification of the process's configuration, including its name and schema. "
            "This helps consumers understand how to configure the process.",
        ),
    ]
    human_inputs: Annotated[
        list[HumanInSpecs], Field(description="List of human work events that the process can receive.")
    ]
    program_inputs: Annotated[
        list[ProgramInSpecs], Field(description="List of program work events that the process can receive.")
    ]
    agent_inputs: Annotated[
        list[AgentInSpecs], Field(description="List of agent work events that the process can receive.")
    ]
    default_process_config: Annotated[ProcessConfig, Field(description="Configuration for the process instance.")]
