from pydantic import Field

from lib_core.nats.events.control.ControlEvent import ControlEvent
from lib_core.nats.events.display.DisplayEvent import DisplayEvent


class ExceptionEvent(ControlEvent, DisplayEvent):
    message: str = Field(..., description="The message of the exception")
