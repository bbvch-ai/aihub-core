from typing import Annotated, Any

from pydantic import BaseModel, Field


class UpdateAgentConfigurationRequest(BaseModel):
    """Request body for updating agent configuration."""

    configuration: Annotated[
        dict[str, Any],
        Field(
            description="The updated configuration values as key-value pairs. "
            "Keys should match the 'name' fields from the agent's form elements."
        ),
    ]
