from typing import Annotated

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
from pydantic import BaseModel, Field

from aihub_api.routes.process.dto.in_specs.AgentInDTO import AgentInDTO
from aihub_api.routes.process.dto.in_specs.HumanInDTO import HumanInDTO
from aihub_api.routes.process.dto.in_specs.ProgramInDTO import ProgramInDTO
from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO


class ProcessDTO(BaseModel):
    """
    An agentic process is a process in which humans, agents and programs interact with each other to achieve a
    common goal.
    To interact with the process, it is necessary to know which entity (human, agent, program) can and must submit
    what kind of work to start / continue the process.
    Hence, this object offers information about the inputs (work events) that these entities can contribute.
    """

    process_class: Annotated[
        str, Field(description="The class or category of the process (e.g., a specific type of process).")
    ]
    process_id: Annotated[str, Field(description="A unique identifier for the process instance.")]
    process_config: Annotated[ProcessConfigDTO, Field(description="Configuration for the process instance.")]
    human_inputs: Annotated[
        list[HumanInDTO], Field(description="List of human work events that the process can receive.")
    ]
    program_inputs: Annotated[
        list[ProgramInDTO], Field(description="List of program work events that the process can receive.")
    ]
    agent_inputs: Annotated[
        list[AgentInDTO],
        Field(
            description="List of agent work events that the process can receive. "
            "Agent work events are used to trigger the execution of an agent."
        ),
    ]
    is_online: Annotated[bool | None, Field(description="Indicates whether the process is online and reachable.")] = (
        None
    )

    @classmethod
    def from_entity(cls, entity: ProcessEntity, t: LocaleHandler, is_online: bool) -> "ProcessDTO":
        human_inputs = [HumanInDTO.from_entity_specs(specs, t) for specs in entity.human_inputs]

        program_inputs = [ProgramInDTO.from_entity_specs(specs) for specs in entity.program_inputs]

        agent_inputs = [AgentInDTO.from_entity_specs(specs, t) for specs in entity.agent_inputs]

        return cls(
            process_class=entity.process_class,
            process_id=entity.process_id,
            process_config=ProcessConfigDTO.from_process_entity_config(entity.process_config, t),
            human_inputs=human_inputs,
            program_inputs=program_inputs,
            agent_inputs=agent_inputs,
            is_online=is_online,
        )
