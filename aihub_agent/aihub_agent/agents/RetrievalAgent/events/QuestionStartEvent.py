from typing import Annotated, Literal

from aihub_lib.generative_ai.retrievers import RetrieverConfig
from aihub_lib.nats.events.control.start import StartEvent
from pydantic import Field


class QuestionStartEvent(StartEvent):
    """
    Start event for the RetrievalAgent containing the query to retrieve for.

    Optionally includes retriever configurations that override the agent's
    configured retrievers when provided.
    """

    question: Annotated[str, Field(..., description="The query that initiates the retrieval workflow.")]
    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language of the user.")] = "en"
    retrievers: Annotated[
        list[RetrieverConfig] | None,
        Field(description="Optional retriever configs. If provided, overrides agent config."),
    ] = None
