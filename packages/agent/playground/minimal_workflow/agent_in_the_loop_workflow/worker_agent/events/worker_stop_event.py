from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import StopEvent


class WorkerStopEvent(StopEvent):
    result: Annotated[int, Field(description="The final result produced by the worker agent")]
