from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events import UserMessageEvent
from swiss_ai_hub.core.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig


class BotInTheLoopAgentStartEvent(UserMessageEvent):
    channel_config: Annotated[SlackConfig | TeamsConfig, Field(description="Slack or Teams configuration for the bot.")]
