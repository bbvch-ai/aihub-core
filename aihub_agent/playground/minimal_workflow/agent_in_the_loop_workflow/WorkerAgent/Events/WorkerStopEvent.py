from pydantic import Field

from aihub_lib.nats.events import StopEvent


class WorkerStopEvent(StopEvent):
    result: int = Field(...)
