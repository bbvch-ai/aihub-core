from typing import Annotated

from aihub_lib.nats.events import StopEvent
from pydantic import Field


class AnswerStopEvent(StopEvent):
    expert_answer: Annotated[str, Field(..., description="The answer to the question")]
