from typing import Annotated
from pydantic import Field

from aihub_lib.nats.events import StopEvent


class OrchestrationResultEvent(StopEvent):
    result: Annotated[int, Field(description="The final result of the orchestration process")]
