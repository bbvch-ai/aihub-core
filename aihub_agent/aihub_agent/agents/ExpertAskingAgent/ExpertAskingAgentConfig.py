from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig
from pydantic import Field, model_validator


class ExpertAskingAgentConfig(AgentConfig):
    llm: LLMConfig
    loop_max: Annotated[int, Field(description="Maximum number of loops to ask experts", gt=0)] = 3
    channel_config: Annotated[TeamsConfig | SlackConfig, Field(description="Teams or Slack configuration for the bot.")]
