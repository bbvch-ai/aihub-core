from typing import Annotated

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.nats.events.discovery.process.ProcessDiscoveryResponseEvent import (
    AgentInSpecs,
    HumanInSpecs,
    ProgramInSpecs,
)
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
from pydantic import BaseModel, Field

from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO


class ProcessDTO(BaseModel):
    process_class: Annotated[
        str, Field(description="The class or category of the process (e.g., a specific type of process).")
    ]
    process_id: Annotated[str, Field(description="A unique identifier for the process instance.")]
    process_config: Annotated[ProcessConfigDTO, Field(description="Configuration for the process instance.")]
    human_inputs: Annotated[
        list[HumanInSpecs], Field(description="List of human work events that the process can receive.")
    ]
    program_inputs: Annotated[
        list[ProgramInSpecs], Field(description="List of program work events that the process can receive.")
    ]
    agent_inputs: Annotated[
        list[AgentInSpecs],
        Field(
            description="List of agent work events that the process can receive. "
            "Agent work events are used to trigger the execution of an agent."
        ),
    ]
    is_online: Annotated[bool | None, Field(description="Indicates whether the agent is online and reachable.")] = None

    @classmethod
    def from_entity(cls, entity: ProcessEntity, t: LocaleHandler, is_online: bool) -> "ProcessDTO":
        human_inputs = [
            HumanInSpecs(
                route=spec.route,
                method=spec.method,
                is_process_start=spec.is_process_start,
                event_specs=EventSpecs(
                    event_name=spec.event_specs.event_name,
                    event_schema=spec.event_specs.event_schema,
                    event_parents=spec.event_specs.event_parents,
                ),
            )
            for spec in entity.human_inputs
        ]

        program_inputs = [
            ProgramInSpecs(
                route=spec.route,
                method=spec.method,
                is_process_start=spec.is_process_start,
                event_specs=EventSpecs(
                    event_name=spec.event_specs.event_name,
                    event_schema=spec.event_specs.event_schema,
                    event_parents=spec.event_specs.event_parents,
                ),
            )
            for spec in entity.program_inputs
        ]

        agent_inputs = [
            AgentInSpecs(
                agent_class=spec.agent_class,
                agent_id=spec.agent_id,
                is_process_start=spec.is_process_start,
                event_specs=EventSpecs(
                    event_name=spec.event_specs.event_name,
                    event_schema=spec.event_specs.event_schema,
                    event_parents=spec.event_specs.event_parents,
                ),
            )
            for spec in entity.agent_inputs
        ]

        return cls(
            process_class=entity.process_class,
            process_id=entity.process_id,
            process_config=ProcessConfigDTO.from_process_config(entity.process_config, t),
            human_inputs=human_inputs,
            program_inputs=program_inputs,
            agent_inputs=agent_inputs,
            is_online=is_online,
        )
