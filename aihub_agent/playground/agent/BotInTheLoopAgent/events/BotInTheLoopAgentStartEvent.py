from typing import Annotated

from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig
from pydantic import Field


class BotInTheLoopAgentStartEvent(UserMessageEvent):
    channel_config: Annotated[SlackConfig | TeamsConfig, Field(description="Slack or Teams configuration for the bot.")]
