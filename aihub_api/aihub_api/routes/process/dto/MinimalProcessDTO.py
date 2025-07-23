from typing import Annotated

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.process import ProcessEntity
from aihub_lib.processes.ProcessConfig import ProcessConfig
from pydantic import BaseModel, Field

from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO


class MinimalProcessDTO(BaseModel):
    """
    A minimal data transfer object for representing process information in responses.
    This DTO contains only the core process information that is typically needed
    for lightweight responses or simple process identification.
    """

    process_class: Annotated[
        str, Field(description="The class or category of the process (e.g., a specific type of process).")
    ]
    process_id: Annotated[str, Field(description="A unique identifier for the process instance.")]
    process_config: Annotated[ProcessConfigDTO, Field(description="Configuration for the process instance.")]

    @classmethod
    def from_entity(cls, entity: ProcessEntity, t: LocaleHandler) -> "MinimalProcessDTO":
        """Converts an ProcessEntity to an ProcessDTO."""
        process_config = ProcessConfig.from_entity(entity.process_config or entity.default_process_config)
        process_config_dto = ProcessConfigDTO.from_process_config(process_config, t)
        return cls(
            process_class=entity.process_class,
            process_id=entity.process_id,
            process_config=process_config_dto,
        )
