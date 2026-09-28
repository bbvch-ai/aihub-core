from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.user.chat_feature import ChatFeature


class OnlineAgent(BaseModel):
    """Agent instance currently online and available for OpenWebUI provisioning."""

    agent_class: Annotated[str, Field(description="The agent class name")]
    agent_id: Annotated[str, Field(description="The agent instance ID")]
    display_name: Annotated[str, Field(description="Human-readable name shown in OpenWebUI")]
    supported_features: Annotated[
        list[ChatFeature],
        Field(description="Chat features the agent's blueprint supports, deciding which toggles it shows"),
    ] = []
