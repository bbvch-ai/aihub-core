from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import Select
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ToolApprovalRule(Form):
    """How one tool's calls are approved on this profile."""

    tool: Annotated[str | Select, Field(description="The tool's name, as the model calls it.")]
    policy: Annotated[ToolApprovalPolicy | Select, Field(description="When the user must approve a call of the tool.")]

    @classmethod
    def as_form(cls, tool_names: list[str]) -> Self:
        return cls(
            tool=Select(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.approval_tool.label"),
                options=[{"label": name, "value": name} for name in tool_names],
                option_label="label",
                option_value="value",
                filter=True,
            ),
            policy=Select(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.approval_policy.label"),
                options=[
                    {
                        "label": AgentLocaleString.from_i18n_path(f"agent.tool_loop.config.policies.{policy.value}"),
                        "value": policy.value,
                    }
                    for policy in ToolApprovalPolicy
                ],
                option_label="label",
                option_value="value",
            ),
        )
