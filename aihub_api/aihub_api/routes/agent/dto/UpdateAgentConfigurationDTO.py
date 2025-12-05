from typing import Annotated, Any

from pydantic import BaseModel, Field


class UpdateAgentConfigurationDTO(BaseModel):
    """Request body for updating agent configuration."""

    configuration: Annotated[
        dict[str, Any],
        Field(
            description="The configuration values to update as key-value pairs. "
            "Keys should match the 'name' fields from the agent's form elements."
        ),
    ]