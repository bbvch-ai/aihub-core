from typing import Annotated, Literal

from aihub_lib.nats.events.control.start import StartEvent
from pydantic import Field


class KnowledgeRetrievalStartEvent(StartEvent):
    """
    Start event for the KnowledgeRetrievalAgent containing the query to retrieve for.

    Optionally includes namespace overrides that replace the bucket's default namespaces.
    """

    question: Annotated[str, Field(..., description="The query that initiates the retrieval workflow.")]
    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language of the user.")] = "en"
    namespaces: Annotated[
        list[str] | None,
        Field(description="Optional namespace override. If provided, replaces bucket's configured namespaces."),
    ] = None
