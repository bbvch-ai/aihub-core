from typing import Annotated

from aihub_lib.nats.events.discovery import ProcessInstanceDiscoveryResponseEvent
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
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
    def from_class_and_config(cls, class_dto: ProcessClassDTO, process_config: ProcessConfig) -> "ProcessInstanceDTO":
        """Creates a ProcessInstanceDTO from a ProcessClassDTO and a ProcessConfig."""
        return cls(
            process_class=class_dto.process_class,
            process_id=process_config.process_id,
            process_config=process_config,
            process_config_specs=class_dto.process_config_specs,
            human_inputs=class_dto.human_inputs,
            program_inputs=class_dto.program_inputs,
            agent_inputs=class_dto.agent_inputs,
            is_online=class_dto.is_online,
            default_process_config=class_dto.default_process_config,
        )

    def to_discovery_response_event(self) -> ProcessInstanceDiscoveryResponseEvent:
        return ProcessInstanceDiscoveryResponseEvent(
            process_class=self.process_class,
            process_id=self.process_id,
            process_config=self.process_config,
            default_process_config=self.default_process_config,
            process_config_specs=self.process_config_specs,
            human_inputs=self.human_inputs,
            program_inputs=self.program_inputs,
            agent_inputs=self.agent_inputs,
        )

    def create_or_update_process_entity(self) -> ProcessEntity:
        return ProcessEntity.create_or_update(
            process_id=self.process_id,
            process_class=self.process_class,
            default_process_config=self.default_process_config,
            human_inputs=self.human_inputs,
            program_inputs=self.program_inputs,
            agent_inputs=self.agent_inputs,
        )
