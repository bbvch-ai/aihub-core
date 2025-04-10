from typing import Annotated

from aihub_lib.nats.events import StopEvent
from pydantic import Field


class AnswerStopEvent(StopEvent):
    """Event representing the conclusion of an expert's response to a user's question."""
    expert_answer: Annotated[str, Field(..., description="The answer to the question")]
