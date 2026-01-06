from typing import Annotated, Any

from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    """Request body for creating a new agent instance."""

    agent_class: Annotated[
        str,
        Field(
            description="The agent class to create an instance of. Must match a discovered/online agent class.",
        ),
    ]
    agent_id: Annotated[
        str,
        Field(
            description="Unique identifier for the agent instance. Must be URL-safe.",
            pattern=r"^[a-z0-9_-]+$",
            min_length=1,
            max_length=100,
        ),
    ]
    configuration: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="The full configuration values including name, description, icon, and runtime settings. "
            "Keys should match the 'name' fields from the agent's form elements.",
        ),
    ]
