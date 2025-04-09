from pydantic import Field

from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import BotInTheLoopRequestEvent
from aihub_lib.nats.events.control.ControlEvent import ControlEvent


class BotInTheLoopResponseEvent(ControlEvent):
    """
    A response from a bot operator after a HITL request.

    ### Why BotInTheLoopResponseEvent?
    Once a bot operator provides an answer to a `BotInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), resuming or altering execution based on bot input.
    """

    response: str = Field(..., description="The bot operator's answer or decision.")
    request_event: BotInTheLoopRequestEvent = Field(
        ...,
        description="The original `BotInTheLoopRequestEvent` that led to this response, providing context for where and why the workflow paused.",
    )
