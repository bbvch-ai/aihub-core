from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import InputNumber, MultiSelect
from swiss_ai_hub.core.form.constraints import Ge
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_rule import ToolApprovalRule
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ToolLoopConfig(Form):
    """Bounds and permissions for the loop in which the model decides which tools to use."""

    max_iterations: Annotated[
        int | InputNumber,
        Field(description="How many times the model may decide on tools before it must answer with what it has."),
        Ge(1),
    ] = 10
    max_tool_calls: Annotated[
        int | InputNumber, Field(description="How many tool calls a run may make in total."), Ge(1)
    ] = 20
    max_result_tokens: Annotated[
        int,
        Field(description="A tool result's size in tokens beyond which it is cut, so results cannot flood the prompt."),
        Ge(1),
    ] = 4000
    disabled_tools: Annotated[
        list[str] | MultiSelect, Field(description="Tools of the blueprint this profile never offers, by name.")
    ] = []
    approvals: Annotated[
        list[ToolApprovalRule],
        Field(
            description="Tools whose calls the user must approve, overriding each tool's own default.",
            title="Approvals",
        ),
    ] = []

    def approval_rule_for(self, tool: str) -> ToolApprovalRule | None:
        return next((rule for rule in self.approvals if rule.tool == tool), None)

    @classmethod
    def as_form(cls, tool_names: list[str]) -> Self:
        """The blueprint's tool names are the options, since which tools exist is the blueprint's to declare."""
        return cls(
            max_iterations=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.max_iterations.label"),
                help=AgentLocaleString.from_i18n_path("agent.tool_loop.config.max_iterations.help"),
                min=1,
                max=50,
                step=1,
            ),
            max_tool_calls=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.max_tool_calls.label"),
                help=AgentLocaleString.from_i18n_path("agent.tool_loop.config.max_tool_calls.help"),
                min=1,
                max=100,
                step=1,
            ),
            disabled_tools=MultiSelect(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.disabled_tools.label"),
                help=AgentLocaleString.from_i18n_path("agent.tool_loop.config.disabled_tools.help"),
                options=[{"label": name, "value": name} for name in tool_names],
                option_label="label",
                option_value="value",
            ),
            approvals=[ToolApprovalRule.as_form(tool_names)],
        )
