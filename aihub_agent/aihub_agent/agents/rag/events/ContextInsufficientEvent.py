from pydantic import Field

from aihub_lib.nats.events import ControlEvent


class ContextInsufficientEvent(ControlEvent):
    reasoning: str = Field(..., description="The reasoning that this event is insufficient.")
