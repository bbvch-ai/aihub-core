from typing import Annotated

from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from pydantic import BaseModel, Field

from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.process.ProcessDiscoveryResponseEvent import ProcessInSpecs
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity


class ProcessDTO(BaseModel):
    process_class: Annotated[
        str, Field(description="The class or category of the process (e.g., a specific type of process).")
    ]
    process_id: Annotated[str, Field(description="A unique identifier for the process instance.")]
    process_config: Annotated[ProcessConfigDTO, Field(description="Configuration for the process instance.")]
    human_inputs: Annotated[
        list[ProcessInSpecs], Field(description="List of human work events that the process can receive.")
    ]
    program_inputs: Annotated[
        list[ProcessInSpecs], Field(description="List of program work events that the process can receive.")
    ]
    is_online: Annotated[bool | None, Field(description="Indicates whether the agent is online and reachable.")] = None

    @classmethod
    def from_entity(cls, entity: ProcessEntity, t: LocaleHandler, is_online: bool | None = None) -> "ProcessDTO":
        human_inputs = [ProcessInSpecs(
            route=spec.route,
            method=spec.method,
            is_process_start=spec.is_process_start,
            event_specs=EventSpecs(event_name=spec.event_specs.event_name, event_schema=spec.event_specs.event_schema),
        ) for spec in entity.human_inputs]

        program_inputs = [ProcessInSpecs(
            route=spec.route,
            method=spec.method,
            is_process_start=spec.is_process_start,
            event_specs=EventSpecs(event_name=spec.event_specs.event_name, event_schema=spec.event_specs.event_schema),
        ) for spec in entity.program_inputs]

        return cls(
            process_class=entity.process_class,
            process_id=entity.process_id,
            process_config=ProcessConfigDTO.from_process_config(entity.process_config, t),
            human_inputs=human_inputs,
            program_inputs=program_inputs,
            is_online=is_online,
        )