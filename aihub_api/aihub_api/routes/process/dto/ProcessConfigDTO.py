from typing import Annotated, Self

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.processes.ProcessConfig import ProcessConfig
from pydantic import BaseModel, Field


class ProcessConfigDTO(BaseModel):
    process_id: Annotated[
        str, Field(description="Used to uniquely identify this process instance.", pattern=r"^[a-z0-9_-]+$")
    ]
    name: Annotated[str, Field(description="The name of the process.")]
    description: Annotated[str, Field(description="The description of the process.")]
    icon: Annotated[str, Field(description="The icon representing the agent.")] = "mage:robot"

    @classmethod
    def from_process_config(cls, process_config: ProcessConfig, t: LocaleHandler) -> Self:
        return cls(
            process_id=process_config.process_id,
            name=t.extract(process_config.name),
            description=t.extract(process_config.description),
            icon=process_config.icon,
        )
