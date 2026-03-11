from typing import Annotated

from pydantic import BaseModel, Field


class OnlineAgent(BaseModel):
    """Agent instance currently online and available for OpenWebUI provisioning."""

    agent_class: Annotated[str, Field(description="The agent class name")]
    agent_id: Annotated[str, Field(description="The agent instance ID")]
    display_name: Annotated[str, Field(description="Human-readable name shown in OpenWebUI")]
