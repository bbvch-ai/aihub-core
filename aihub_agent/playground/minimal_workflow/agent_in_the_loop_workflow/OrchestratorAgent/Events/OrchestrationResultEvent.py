from typing import Annotated

from aihub_lib.nats.events import StopEvent
from pydantic import Field


class OrchestrationResultEvent(StopEvent):
    result: Annotated[int, Field(description="The final result of the orchestration process")]
