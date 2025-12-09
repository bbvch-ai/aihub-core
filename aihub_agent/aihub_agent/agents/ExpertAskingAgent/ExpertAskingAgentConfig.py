from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig
from pydantic import Field, model_validator


class ExpertAskingAgentConfig(AgentConfig):
    llm: LLMConfig
    loop_max: Annotated[int, Field(description="Maximum number of loops to ask experts", gt=0)] = 3
    teams_config: Annotated[TeamsConfig | None, Field(description="Teams configuration for the bot.")] = None
    slack_config: Annotated[SlackConfig | None, Field(description="Slack configuration for the bot.")] = None

    @model_validator(mode="after")
    def validate_exclusive_config(self) -> "ExpertAskingAgentConfig":
        has_teams = self.teams_config is not None
        has_slack = self.slack_config is not None

        if not has_teams and not has_slack:
            raise ValueError("Either teams_config or slack_config must be provided")

        if has_teams and has_slack:
            raise ValueError("Only one of teams_config or slack_config can be provided, not both")

        return self
