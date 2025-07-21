from typing import Annotated, Any

from pydantic import BaseModel, Field

from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessConfigSpecs(BaseModel):
    """
    Defines a specification for a process's configuration.
    """

    process_config_schema: Annotated[
        dict[str, Any],
        Field(
            description="A dictionary describing the schema of the process configuration, providing details about "
            "expected fields and their types. This helps external consumers understand how to "
            "construct and validate process configurations.",
        ),
    ]

    @classmethod
    def from_process_config_class(cls, process_config_class: type[ProcessConfig]):
        return cls(
            process_config_schema=process_config_class.model_json_schema(),
        )
