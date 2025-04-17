from typing import Dict, Optional, ClassVar

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import BotInTheLoopRequestEvent
from aihub_lib.nats.events.control.ControlEvent import ControlEvent


class SlackResponderInfo(BaseModel):
    """
    Information about a Slack user who responded to a BITL request.
    """

    user_id: str = Field(..., description="The Slack user ID.")
    user_name: Optional[str] = Field(None, description="The Slack user name.")
    additional_info: Optional[Dict] = Field(None, description="Additional Slack-specific user information.")


class BotInTheLoopResponseEvent(ControlEvent):
    """
    A response from a bot operator after a HITL request.

    ### Why BotInTheLoopResponseEvent?
    Once a bot operator provides an answer to a `BotInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), resuming or altering execution based on bot input.
    """
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.bitl_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.bitl_response_event.description")

    response: str = Field(..., description="The bot operator's answer or decision.")
    request_event: BotInTheLoopRequestEvent = Field(
        ...,
        description="The original `BotInTheLoopRequestEvent` that led to this response, providing context for where and why the workflow paused.",
    )
    responder: Optional[SlackResponderInfo] = Field(
        None,
        description="Information about the Slack user who responded to the request, enabling tracking of who provided the input.",
    )
