from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent.bitl.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig
from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent


class BotInTheLoopAgentStartEvent(UserMessageEvent):
    channel_config: Annotated[SlackConfig | TeamsConfig, Field(description="Slack or Teams configuration for the bot.")]
