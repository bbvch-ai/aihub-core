from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.processes import ProcessConfig


class ProcessConfigDTO(BaseModel):
    process_id: Annotated[
        str, Field(description="Used to uniquely identify this process instance.", pattern=r"^[a-z0-9_-]+$")
    ]
    name: Annotated[str, Field(description="The name of the process.")]
    description: Annotated[str, Field(description="The description of the process.")]
    icon: Annotated[str, Field(description="The icon representing the process.")] = "mage:arrowlist"

    @classmethod
    def from_process_config(cls, process_config: ProcessConfig, t: LocaleHandler) -> Self:
        return cls(
            process_id=process_config.process_id,
            name=t.extract(process_config.name),
            description=t.extract(process_config.description),
            icon=process_config.icon,
        )
