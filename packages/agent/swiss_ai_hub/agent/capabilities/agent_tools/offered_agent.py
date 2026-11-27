from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy


class OfferedAgent(BaseModel):
    """An agent offered to the model in this run under a tool name; calls resolve their target from it alone."""

    tool_name: Annotated[str, Field(description="The tool the model calls the agent by.")]
    agent_class: Annotated[str, Field(description="The agent's class.")]
    agent_id: Annotated[str, Field(description="The agent's profile.")]
    name: Annotated[LocaleString, Field(description="The profile's name, the tool's label.")]
    approval: Annotated[ToolApprovalPolicy, Field(description="When a call needs the user's approval.")]
