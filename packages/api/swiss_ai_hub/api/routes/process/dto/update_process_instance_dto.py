from typing import Annotated, Any

from pydantic import BaseModel, Field


class UpdateProcessInstanceDTO(BaseModel):
    """Request body for updating a process instance configuration."""

    configuration: Annotated[
        dict[str, Any],
        Field(
            description="The configuration values to update as key-value pairs. "
            "Keys should match the 'name' fields from the process's form elements."
        ),
    ]
