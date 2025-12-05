"""Configuration for MongoDB text search based insight retrieval."""

from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.generative_ai.knowledge.BaseRetrieverConfig import BaseRetrieverConfig


class InsightRetrieverConfig(BaseRetrieverConfig):
    """
    Configuration for MongoDB text search based insight retrieval.

    Uses simple text search on InsightEntity (title + content fields)
    instead of vector embeddings. This is faster and simpler for
    insights which are already structured expert knowledge.
    """

    retriever_type: Literal["insight"] = "insight"

    namespace: Annotated[
        str | None,
        Field(description="Namespace to filter insights (None for all)."),
    ] = None
    max_results: Annotated[
        int,
        Field(description="Maximum number of insights to retrieve.", ge=1),
    ] = 10
