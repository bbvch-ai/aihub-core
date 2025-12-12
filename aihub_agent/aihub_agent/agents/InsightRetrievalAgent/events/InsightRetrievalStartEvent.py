from typing import Annotated, Literal

from aihub_lib.generative_ai.retrievers import InsightSourceConfig
from aihub_lib.nats.events.control.start import StartEvent
from pydantic import Field


class InsightRetrievalStartEvent(StartEvent):
    """
    Start event for the InsightRetrievalAgent containing the query to retrieve for.

    Optionally includes source overrides that replace the agent's default sources.
    """

    question: Annotated[str, Field(..., description="The query that initiates the retrieval workflow.")]
    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language of the user.")] = "en"
    sources: Annotated[
        list[InsightSourceConfig] | None,
        Field(description="Optional source override. If provided, replaces agent's configured sources."),
    ] = None
