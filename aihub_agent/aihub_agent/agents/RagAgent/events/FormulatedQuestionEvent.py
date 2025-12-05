"""Event containing a formulated question for the expert."""

from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class FormulatedQuestionEvent(ControlEvent):
    """Event containing a formulated question for the expert based on missing context."""

    question: Annotated[str, Field(description="The formulated question for the expert")]
