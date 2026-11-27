from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.form import AgentSelector, Select
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy


class AgentToolChoice(Form):
    """One agent a profile names for its model to call, and when such a call needs the user's approval."""

    agent: Annotated[AgentRef | AgentSelector, Field(description="The agent profile the model may call.")]
    approval: Annotated[
        ToolApprovalPolicy | Select, Field(description="When a call to this agent needs the user's approval.")
    ] = ToolApprovalPolicy.NEVER
