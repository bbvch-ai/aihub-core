from typing import Annotated, Literal, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import SlackConfig, TeamsConfig
from swiss_ai_hub.core.form import InputNumber, LocaleInput, Select
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import LLMConfig, OrgMemoryWriteConfig
from swiss_ai_hub.core.i18n import LocaleString

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
    task_llm: Annotated[
        LLMConfig | None,
        Field(
            default=None,
            description=(
                "Model for this agent's auxiliary steps: routing the conversation to the next workflow "
                "branch, and refining the follow-up question sent to the expert. Generation parameters are "
                "inherited from the main model. Falls back to the main model when disabled."
            ),
            title="Task LLM",
        ),
    ] = None
    loop_max: Annotated[
        int | InputNumber,
        Field(description="Maximum number of loops to ask experts."),
        Gt(0),
    ] = 3
    org_memory: Annotated[
        OrgMemoryWriteConfig,
        Field(
            description="Configuration for organization-memory scoping.",
            title="Organization Memory",
        ),
    ] = OrgMemoryWriteConfig()
    org_memory_format: Annotated[
        LocaleString | LocaleInput,
        Field(
            description=(
                "Template for the Q&A snippet stored in organization memory."
                " Supports {question} and {answer} as placeholders."
            ),
            title="Organization Memory Format",
        ),
    ] = AgentLocaleString.from_i18n_path("agent.expert_asking_agent.config.org_memory_format.default")

    channel_config: Annotated[
        ChannelConfig,
        Field(title="Channel Configuration", description="Configuration for the expert escalation channel."),
    ]

    @model_validator(mode="after")
    def derive_task_llm_from_main_llm(self) -> Self:
        """Only the task model is configurable: its generation parameters always mirror the main llm, and
        an unset or blank picker falls back to the main model."""
        if not isinstance(self.llm.model_name, str):
            return self
        task_model_name = self.task_llm.model_name if self.task_llm else None
        self.task_llm = self.llm.as_task_llm(task_model_name or self.llm.model_name)
        return self

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
            task_llm=LLMConfig.as_form(include_default_parameter=False),
            loop_max=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.config.loop_max.label"),
                min=1,
                max=10,
                step=1,
            ),
            channel_config=ChannelConfig.as_form(),
            org_memory=OrgMemoryWriteConfig.as_form(),
            org_memory_format=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.config.org_memory_format.label"),
                help_text=AgentLocaleString.from_i18n_path("agent.expert_asking_agent.config.org_memory_format.help"),
                input_type="textarea",
            ),
        )

    def get_active_channel_config(self) -> TeamsConfig | SlackConfig | None:
        """Helper to get the active channel config based on channel_type."""
        return self.channel_config.get_active_config()
