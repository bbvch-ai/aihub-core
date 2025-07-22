from typing import Annotated

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
