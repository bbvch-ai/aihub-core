from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig, SlackConfig
from aihub_lib.nats.events.control.start.StartEvent import StartEvent
from aihub_lib.nats.events.user.UserUploadedFile import UserUploadedFile


class BotInTheLoopAgentStartEvent(StartEvent):
    teams_config: Annotated[TeamsConfig | None, Field(description="Teams configuration for the bot.")] = None
    slack_config: Annotated[SlackConfig | None, Field(description="Slack configuration for the bot.")] = None
