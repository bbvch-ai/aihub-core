from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig, SlackConfig


class BotInTheLoopAgentStartEvent(UserMessageEvent):
    teams_config: Annotated[TeamsConfig | None, Field(description="Teams configuration for the bot.")] = None
    slack_config: Annotated[SlackConfig | None, Field(description="Slack configuration for the bot.")] = None
