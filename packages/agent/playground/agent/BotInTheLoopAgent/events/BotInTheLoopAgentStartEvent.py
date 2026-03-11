from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import SlackConfig, TeamsConfig, UserMessageEvent


class BotInTheLoopAgentStartEvent(UserMessageEvent):
    channel_config: Annotated[SlackConfig | TeamsConfig, Field(description="Slack or Teams configuration for the bot.")]
