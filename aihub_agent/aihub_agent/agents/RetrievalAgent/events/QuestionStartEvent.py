from typing import Annotated, Literal

from aihub_lib.nats.events.control.start import StartEvent
from pydantic import Field


class QuestionStartEvent(StartEvent):
    """
    Start event for the RetrievalAgent containing the query to retrieve for.
    """

    question: Annotated[str, Field(..., description="The query that initiates the retrieval workflow.")]
    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language of the user.")] = "en"
