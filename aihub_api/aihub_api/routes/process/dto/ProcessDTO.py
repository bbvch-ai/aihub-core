from typing import Annotated

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.nats.events.discovery.process.agent_in.AgentInSpecs import AgentInSpecs
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.discovery.process.program_in.ProgramInSpecs import ProgramInSpecs
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
from aihub_lib.processes.ProcessConfig import ProcessConfig
from pydantic import Field

from aihub_api.routes.process.dto.MinimalProcessDTO import MinimalProcessDTO
from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO
from aihub_api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO


class ProcessDTO(MinimalProcessDTO):
    """
    A data transfer object for representing process information in responses.
    This DTO standardizes how process data is returned from the service layer to the controller,
    and subsequently to the API response. It helps maintain a clean separation between the internal
    event models and the publicly exposed fields in HTTP responses.
    By using `ProcessDTO`, the API can evolve independently from the internal event representations.
    """

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
    is_online: Annotated[bool | None, Field(description="Indicates whether the process is online and reachable.")] = (
        None
    )

    @classmethod
    def from_instance(
        cls, instance: ProcessInstanceDTO, t: LocaleHandler, is_online: bool | None = None
    ) -> "ProcessDTO":
        """Creates a ProcessDTO from a ProcessInstanceDTO."""
        return cls(
            process_class=instance.process_class,
            process_id=instance.process_id,
            process_config=ProcessConfigDTO.from_process_config(instance.process_config, t),
            human_inputs=instance.human_inputs,
            program_inputs=instance.program_inputs,
            agent_inputs=instance.agent_inputs,
            is_online=is_online,
        )

    @classmethod
    def from_entity(cls, entity: ProcessEntity, t: LocaleHandler, is_online: bool | None = None) -> "ProcessDTO":
        """Converts a ProcessEntity to a ProcessDTO."""
        process_config = ProcessConfig.from_entity(entity.process_config or entity.default_process_config)
        process_config_dto = ProcessConfigDTO.from_process_config(process_config, t)

        human_inputs = [
            HumanInSpecs(
                name=spec.name,
                description=spec.description,
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
            process_config=process_config_dto,
            human_inputs=human_inputs,
            program_inputs=program_inputs,
            agent_inputs=agent_inputs,
            is_online=is_online,
        )
