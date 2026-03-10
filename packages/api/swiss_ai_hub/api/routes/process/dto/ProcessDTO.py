from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler

from swiss_ai_hub.api.routes.process.dto.in_specs.AgentInDTO import AgentInDTO
from swiss_ai_hub.api.routes.process.dto.in_specs.HumanInDTO import HumanInDTO
from swiss_ai_hub.api.routes.process.dto.in_specs.ProgramInDTO import ProgramInDTO
from swiss_ai_hub.api.routes.process.dto.MinimalProcessDTO import MinimalProcessDTO
from swiss_ai_hub.api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO
from swiss_ai_hub.api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO


class ProcessDTO(MinimalProcessDTO):
    """
    A data transfer object for representing process information in responses.
    This DTO standardizes how process data is returned from the service layer to the controller,
    and subsequently to the API response. It helps maintain a clean separation between the internal
    event models and the publicly exposed fields in HTTP responses.
    By using `ProcessDTO`, the API can evolve independently from the internal event representations.
    """

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
    def from_instance(cls, instance: ProcessInstanceDTO, t: LocaleHandler, is_online: bool) -> Self:
        """Creates a ProcessDTO from a ProcessInstanceDTO."""
        return cls(
            process_class=instance.process_class,
            process_id=instance.process_id,
            process_config=ProcessConfigDTO.from_process_config(instance.process_config, t),
            human_inputs=[HumanInDTO.from_human_in_specs(human_in, t=t) for human_in in instance.human_inputs],
            program_inputs=[ProgramInDTO.from_program_in_specs(program_in) for program_in in instance.program_inputs],
            agent_inputs=[AgentInDTO.from_agent_in_specs(agent_in, t=t) for agent_in in instance.agent_inputs],
            is_online=is_online,
        )
