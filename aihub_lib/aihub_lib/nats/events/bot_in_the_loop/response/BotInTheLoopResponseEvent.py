from pydantic import Field

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent


class BotInTheLoopResponseEvent(ControlEvent):
    """
    A response from a human operator after a HITL request.

    ### Why HumanInTheLoopResponseEvent?
    Once a human operator provides an answer to a `HumanInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), resuming or altering execution based on human input.
    """

    response: str = Field(..., description="The human operator's answer or decision.")
    request_event: HumanInTheLoopRequestEvent = Field(
        ...,
        description="The original `HumanInTheLoopRequestEvent` that led to this response, providing context for where and why the workflow paused.",
    )
