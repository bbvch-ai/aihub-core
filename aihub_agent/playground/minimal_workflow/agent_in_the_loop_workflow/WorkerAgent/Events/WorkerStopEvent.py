from typing import Annotated
from pydantic import Field

from aihub_lib.nats.events import StopEvent


class WorkerStopEvent(StopEvent):
    result: Annotated[int, Field()]
