from typing import Annotated

from aihub_lib.nats.events import StopEvent
from pydantic import Field


class WorkerStopEvent(StopEvent):
    result: Annotated[int, Field(description="The final result produced by the worker agent")]
