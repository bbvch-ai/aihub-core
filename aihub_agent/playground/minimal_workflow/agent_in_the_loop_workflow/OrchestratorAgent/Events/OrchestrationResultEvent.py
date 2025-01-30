from pydantic import Field

from aihub_lib.nats.events import StopEvent


class OrchestrationResultEvent(StopEvent):
    result: int = Field(...)
