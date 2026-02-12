from typing import Annotated, Self

from aihub_lib.processes.ProcessConfig import ProcessConfig
from pydantic import Field

from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO


class ProcessInstanceDTO(ProcessClassDTO):
    """
    Encapsulates the data transfer object (DTO) for a process instance.
    Contains information about the process instance, including its ID and configuration.
    """

    process_id: Annotated[str, Field(description="Unique identifier for the process instance (e.g., 'process_123').")]
    process_config: Annotated[
        ProcessConfig,
        Field(description="Configuration details of the process, including name, description, and other settings."),
    ]

    @classmethod
    def from_class_and_config(cls, class_dto: ProcessClassDTO, process_config: ProcessConfig) -> Self:
        """Creates a ProcessInstanceDTO from a ProcessClassDTO and a ProcessConfig."""
        return cls(
            process_class=class_dto.process_class,
            name=class_dto.name,
            description=class_dto.description,
            icon=class_dto.icon,
            form=class_dto.form,
            process_id=process_config.process_id,
            process_config=process_config,
            process_config_specs=class_dto.process_config_specs,
            human_inputs=class_dto.human_inputs,
            program_inputs=class_dto.program_inputs,
            agent_inputs=class_dto.agent_inputs,
            is_online=class_dto.is_online,
            default_process_config=class_dto.default_process_config,
        )
