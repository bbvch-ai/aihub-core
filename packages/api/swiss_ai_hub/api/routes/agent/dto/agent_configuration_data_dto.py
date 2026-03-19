from typing import Annotated, Any

from pydantic import BaseModel, Field


class AgentConfigurationDataDTO(BaseModel):
    """Response containing the current configuration data for an agent."""

    agent_class: Annotated[str, Field(description="The agent's class identifier.")]
    agent_id: Annotated[str, Field(description="The agent's instance identifier.")]
    configuration: Annotated[
        dict[str, Any],
        Field(
            description="The current configuration values as key-value pairs. "
            "Keys match the 'name' fields from the agent's form elements."
        ),
    ]
