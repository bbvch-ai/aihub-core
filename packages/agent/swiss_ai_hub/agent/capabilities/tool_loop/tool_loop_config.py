from typing import Annotated, Any, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.form import Checkbox, InputNumber, MultiSelect
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
    disable_tools: Annotated[
        bool | Checkbox, Field(description="Whether this profile withholds some of the blueprint's tools.")
    ] = False
    disabled_tools: Annotated[
        list[str] | MultiSelect,
        Field(description="Tools of the blueprint this profile never offers, by name, while `disable_tools` is on."),
    ] = []
    approvals: Annotated[
        list[ToolApprovalRule],
        Field(
            description="Tools whose calls the user must approve, overriding each tool's own default.",
            title="Approvals",
        ),
    ] = []

    @model_validator(mode="before")
    @classmethod
    def keep_stored_restrictions(cls, data: Any) -> Any:
        """Profiles saved before the checkbox existed hold only the list, and must keep withholding those tools."""
        if isinstance(data, dict) and "disable_tools" not in data and isinstance(data.get("disabled_tools"), list):
            return {**data, "disable_tools": bool(data["disabled_tools"])}
        return data

    def is_disabled(self, tool: str) -> bool:
        """The list only counts while its checkbox is ticked, so unticking it re-offers every tool."""
        return self.disable_tools and tool in self.disabled_tools

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
            disable_tools=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.disable_tools.label"),
                help=AgentLocaleString.from_i18n_path("agent.tool_loop.config.disable_tools.help"),
                ref="check_tool_loop_disable_tools",
            ),
            disabled_tools=MultiSelect(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.disabled_tools.label"),
                help=AgentLocaleString.from_i18n_path("agent.tool_loop.config.disabled_tools.help"),
                options=[{"label": name, "value": name} for name in tool_names],
                option_label="label",
                option_value="value",
                condition_if="$get(check_tool_loop_disable_tools).value",
            ),
            approvals=[ToolApprovalRule.as_form(tool_names)],
        )
