from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.generative_ai.retrievers import RetrievalOverride
from aihub_lib.nats.events.control.start import StartEvent


class RetrievalStartEvent(StartEvent):
    """
    Unified start event for ALL retrieval agents (knowledge, insight, SQL, graph, etc.).

    The override field uses a discriminated union - each retrieval agent type defines its own
    override schema. The agent validates that the override type matches its expected type at runtime.

    Example:
        # Knowledge retrieval with namespace override
        RetrievalStartEvent(
            question="What is the company policy?",
            locale="en",
            override=KnowledgeRetrievalOverride(namespaces=["hr-policies"])
        )

        # Insight retrieval with source override
        RetrievalStartEvent(
            question="What did the expert say?",
            locale="en",
            override=InsightRetrievalOverride(sources=[...])
        )

        # Using agent's default config (no override)
        RetrievalStartEvent(question="Search query", locale="en")
    """

    question: Annotated[str, Field(description="The query that initiates the retrieval workflow.")]
    locale: Annotated[Literal["de", "en", "fr", "it"], Field(description="The language of the user.")] = "en"
    override: Annotated[
        RetrievalOverride | None,
        Field(description="Type-specific runtime override. Must match agent's retrieval type if provided."),
    ] = None
