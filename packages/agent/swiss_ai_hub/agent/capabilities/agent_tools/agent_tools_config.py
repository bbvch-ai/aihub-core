from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.form import Checkbox, InputNumber, Select
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.agent_tools.agent_tool_choice import AgentToolChoice
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy

MIN_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS = 10, 900


class AgentToolsConfig(Form):
    """Which agents a profile's model may call as tools, and how long it waits for one."""

    only_listed: Annotated[
        bool | Checkbox,
        Field(description="Offer only the agents listed below; otherwise every agent the asking user may use."),
    ] = False
    agents: Annotated[
        list[AgentToolChoice],
        Field(description="Agents with an approval policy of their own, and with `only_listed` the only ones offered."),
    ] = []
    default_approval: Annotated[
        ToolApprovalPolicy | Select,
        Field(description="When a call to an agent not listed needs the user's approval."),
    ] = ToolApprovalPolicy.NEVER
    timeout_seconds: Annotated[
        int | InputNumber,
        Field(description="How long the model waits for an agent before it is told the agent did not answer."),
        Ge(MIN_TIMEOUT_SECONDS),
        Le(MAX_TIMEOUT_SECONDS),
    ] = 180
    max_depth: Annotated[
        int,
        Field(
            description="How long a chain of agents calling agents may grow; an agent at the limit is offered none.",
            ge=1,
        ),
    ] = 2

    def choice_for(self, agent_class: str, agent_id: str) -> AgentToolChoice | None:
        return next(
            (choice for choice in self.agents if choice.agent == AgentRef(agent_class=agent_class, agent_id=agent_id)),
            None,
        )

    def admits(self, agent_class: str, agent_id: str) -> bool:
        return not self.only_listed or self.choice_for(agent_class, agent_id) is not None

    def approval_for(self, agent_class: str, agent_id: str) -> ToolApprovalPolicy:
        choice = self.choice_for(agent_class, agent_id)
        return ToolApprovalPolicy(choice.approval if choice else self.default_approval)
