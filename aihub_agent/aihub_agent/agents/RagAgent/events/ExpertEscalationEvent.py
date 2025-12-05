"""Event triggered when expert escalation is needed."""

from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class ExpertEscalationEvent(ControlEvent):
    """
    Event triggered when context is insufficient and expert workflow is enabled.

    Signals that the RAGAgent should escalate to human experts.
    """

    reason: Annotated[str, Field(description="The reason why expert escalation is needed")]
