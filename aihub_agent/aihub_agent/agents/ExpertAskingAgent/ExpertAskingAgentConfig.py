from typing import Annotated, Literal

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.persistence.expert.ExpertGroupEntity import ExpertGroupEntity
from pydantic import Field, model_validator

ExpertChannelType = Literal["bitl", "gui"]


class ExpertAskingAgentConfig(AgentConfig):
    """Configuration for the ExpertAskingAgent."""

    llm: LLMConfig

    expert_channel_type: Annotated[
        ExpertChannelType,
        Field(
            "gui",
            description="The channel type to use for expert communication. "
            "'bitl' uses Slack/Teams, 'gui' uses the built-in web interface.",
        ),
    ] = "gui"

    slack_channel_id: Annotated[
        str | None,
        Field(None, description="Slack channel ID for BitL mode. Required when expert_channel_type is 'bitl'."),
    ] = None

    expert_group: Annotated[
        str,
        Field(
            ExpertGroupEntity.DEFAULT_GROUP_NAME,
            description="Expert group identifier for GUI mode. Used to filter questions by group.",
        ),
    ] = ExpertGroupEntity.DEFAULT_GROUP_NAME

    loop_max: Annotated[int, Field(3, description="Maximum number of loops to ask experts", gt=0)] = 3

    insight_namespace: Annotated[
        str,
        Field("default", description="Namespace for storing insights in MongoDB"),
    ] = "default"

    insight_agent_class: Annotated[
        str | None,
        Field(None, description="Class name of the InsightAgent to trigger after successful answer"),
    ] = None

    insight_agent_id: Annotated[
        str | None,
        Field(None, description="Instance ID of the InsightAgent to trigger after successful answer"),
    ] = None

    @model_validator(mode="after")
    def validate_channel_config(self) -> "ExpertAskingAgentConfig":
        """Validates that required fields are present based on expert_channel_type."""
        if self.expert_channel_type == "bitl" and not self.slack_channel_id:
            raise ValueError("slack_channel_id is required when expert_channel_type is 'bitl'")
        return self
