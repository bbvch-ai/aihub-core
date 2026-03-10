from typing import Annotated, Literal

from pydantic import Field
from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent


class QuestionStartEvent(StartEvent):
    """
    Represents a specialized StartEvent containing only a string question.
    This is typically the initial event to trigger an agent's workflow for question handling.
    """

    question: Annotated[str, Field(..., description="The query that initiates the workflow.")]
    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language of the user.")] = "en"
