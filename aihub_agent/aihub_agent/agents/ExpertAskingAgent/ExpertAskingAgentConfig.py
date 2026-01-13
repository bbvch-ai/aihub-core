from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig
from pydantic import Field


class ExpertAskingAgentConfig(AgentConfig):
    """Configuration for ExpertAskingAgent.

    When used with NamespaceSelectionAgent, namespaces are passed dynamically via the start event.
    When used directly (without namespace selection), default_namespaces is used as fallback.
    """

    llm: LLMConfig
    loop_max: Annotated[int, Field(description="Maximum number of loops to ask experts", gt=0)] = 3
    channel_config: Annotated[TeamsConfig | SlackConfig, Field(description="Teams or Slack configuration for the bot.")]
    default_namespaces: Annotated[
        list[str],
        Field(
            description="Fallback namespaces for storing insights when not provided via event. "
            "Uses compound format 'bucket_name/namespace_name'.",
        ),
    ] = ["default"]
