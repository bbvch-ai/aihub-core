from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent.control.stop.StopEvent import StopEvent


class OrchestrationResultEvent(StopEvent):
    result: Annotated[int, Field(description="The final result of the orchestration process")]
