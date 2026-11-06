from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import Select
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n import LOCALES, LocaleString

from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ToolApprovalRule(Form):
    """How one tool's calls are approved on this profile."""

    tool: Annotated[str | Select, Field(description="The tool's name, as the model calls it.")]
    policy: Annotated[ToolApprovalPolicy | Select, Field(description="When the user must approve a call of the tool.")]

    @classmethod
    def as_form(cls, tool_names: list[str], defaults: dict[str, ToolApprovalPolicy]) -> Self:
        """A tool that asks by default says so in the picker, since a profile without a rule for it still asks."""
        return cls(
            tool=Select(
                label=AgentLocaleString.from_i18n_path("agent.tool_loop.config.approval_tool.label"),
                help=AgentLocaleString.from_i18n_path("agent.tool_loop.config.approval_tool.help"),
                options=[{"label": cls._option_label(name, defaults), "value": name} for name in tool_names],
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

    @staticmethod
    def _option_label(name: str, defaults: dict[str, ToolApprovalPolicy]) -> LocaleString:
        policy = defaults.get(name, ToolApprovalPolicy.NEVER)
        if policy == ToolApprovalPolicy.NEVER:
            return LocaleString(**dict.fromkeys(LOCALES, name))
        path = "agent.tool_loop.config.approval_tool.with_default"
        return LocaleString(
            **{
                locale: AgentLocaleHandler(locale)(
                    path,
                    tool=name,
                    policy=AgentLocaleHandler(locale)(f"agent.tool_loop.config.policies.{policy.value}"),
                )
                for locale in LOCALES
            }
        )
