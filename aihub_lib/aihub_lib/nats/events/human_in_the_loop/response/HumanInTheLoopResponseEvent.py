from pydantic import Field

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent


class HumanInTheLoopResponseEvent(ControlEvent, DisplayEvent):
    """
    A response from a human operator after a HITL request.

    ### Why HumanInTheLoopResponseEvent?
    Once a human operator provides an answer to a `HumanInTheLoopRequestEvent`, the response:
    - Influences the workflow (since it's a `ControlEvent`), resuming or altering execution based on human input.
    - Is visible to the UI (since it's also a `DisplayEvent`), allowing transparency and auditing.
    """

    response: str = Field(..., description="The human operator's answer or decision.")
    request_event: HumanInTheLoopRequestEvent = Field(
        ...,
        description="The original `HumanInTheLoopRequestEvent` that led to this response, providing context for where and why the workflow paused.",
    )
