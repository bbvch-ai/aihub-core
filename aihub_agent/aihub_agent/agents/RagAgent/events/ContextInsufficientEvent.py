from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class ContextInsufficientEvent(ControlEvent):
    """Event indicating that the context is insufficient for the task at hand."""

    reasoning: Annotated[str, Field(..., description="Reasoning for context insufficiency")]
