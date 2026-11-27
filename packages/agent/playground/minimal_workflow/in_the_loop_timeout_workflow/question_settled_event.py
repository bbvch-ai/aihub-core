from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlAndDisplayEvent


class QuestionSettledEvent(ControlAndDisplayEvent):
    """How the confirmation ended: answered either way, or given up on at its deadline."""

    outcome: Annotated[str, Field(description="What the run continues with.")]
