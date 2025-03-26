from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class ContextInsufficientEvent(ControlEvent):
    reasoning: str = Field(..., description="The reasoning that this event is insufficient.")
