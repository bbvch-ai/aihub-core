from pydantic import Field

from aihub_lib.nats.events import ControlEvent


class ExtractNumberEvent(ControlEvent):
    number: int = Field(...)
