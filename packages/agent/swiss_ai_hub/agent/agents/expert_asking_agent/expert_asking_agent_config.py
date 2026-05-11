from typing import Annotated, Literal, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import SlackConfig, TeamsConfig
from swiss_ai_hub.core.form import InputNumber, Select
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import LLMConfig, OrgMemoryWriteConfig

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ChannelConfig(Form):
    """Wrapper config for channel selection with conditional Teams/Slack configuration."""

    channel_type: Annotated[
        Literal["teams", "slack"] | Select,
        Field(description="The communication channel to use for expert escalation."),
    ] = "teams"

    teams_config: Annotated[
        TeamsConfig | None,
        Field(description="Teams channel configuration."),
    ] = None

    slack_config: Annotated[
        SlackConfig | None,
        Field(description="Slack channel configuration."),
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        """Factory method for form-mode ChannelConfig."""
        return cls(
            channel_type=Select(
                label=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.config.channel_type.label"),
                help=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.config.channel_type.help"),
                options=[
                    {
                        "label": AgentLocaleString.from_i18n_path(
                            "agent.expert_asking_agent.config.channel_type.teams_label"
                        ),
                        "value": "teams",
                    },
                    {
                        "label": AgentLocaleString.from_i18n_path(
                            "agent.expert_asking_agent.config.channel_type.slack_label"
                        ),
                        "value": "slack",
                    },
                ],
                option_label="label",
                option_value="value",
                ref="channel_type_selector",
            ),
            teams_config=TeamsConfig.as_form(condition_if="$get(channel_type_selector).value === 'teams'"),
            slack_config=SlackConfig.as_form(condition_if="$get(channel_type_selector).value === 'slack'"),
        )

    def get_active_config(self) -> TeamsConfig | SlackConfig | None:
        """Get the active channel config based on channel_type."""
        if self.channel_type == "slack":
            return self.slack_config
        return self.teams_config


class ExpertAskingAgentConfig(AgentConfig):
    """
    Configuration for ExpertAskingAgent.

    This agent escalates questions to human experts via Teams or Slack.
    The channel type and configuration are now user-configurable through the form.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="LLM configuration for the agent."),
    ]
    loop_max: Annotated[
        int | InputNumber,
        Field(description="Maximum number of loops to ask experts."),
        Gt(0),
    ] = 3
    org_memory: Annotated[
        OrgMemoryWriteConfig | None,
        Field(
            description=(
                "Configuration for organization-memory scoping. Set to null to disable writing "
                "expert conversations to organization memory."
            ),
            title="Organization Memory",
        ),
    ] = Field(default_factory=OrgMemoryWriteConfig)

    channel_config: Annotated[
        ChannelConfig,
        Field(title="Channel Configuration", description="Configuration for the expert escalation channel."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode ExpertAskingAgentConfig - NO ARGUMENTS."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            llm=LLMConfig.as_form(),
            loop_max=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.config.loop_max.label"),
                min=1,
                max=10,
                step=1,
            ),
            channel_config=ChannelConfig.as_form(),
            org_memory=OrgMemoryWriteConfig.as_form(),
        )

    def get_active_channel_config(self) -> TeamsConfig | SlackConfig | None:
        """Helper to get the active channel config based on channel_type."""
        return self.channel_config.get_active_config()
