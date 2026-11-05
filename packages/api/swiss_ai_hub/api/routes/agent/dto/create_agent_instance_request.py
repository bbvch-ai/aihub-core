from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.agents import AgentConfig


class CreateAgentInstanceRequest(BaseModel):
    """
    Request body for creating a new agent instance.
    The agent_class is provided in the URL path, not in the request body.
    """

    agent_id: Annotated[
        str,
        Field(
            description="Unique identifier for the agent instance. Must be URL-safe.",
            pattern=r"^[a-z0-9_-]+$",
            min_length=1,
            max_length=AgentConfig.ID_MAX_LENGTH,
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
