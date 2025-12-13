from typing import Annotated, Literal

from pydantic import BaseModel, Field

from aihub_lib.generative_ai.retrievers.InsightSourceConfig import InsightSourceConfig


class KnowledgeRetrievalOverride(BaseModel):
    """
    Type-safe runtime override for knowledge (vector store) retrieval.

    Used to override which namespaces a KnowledgeRetrievalAgent should search
    at runtime. The 'type' discriminator enables type-safe union handling.
    """

    type: Literal["knowledge"] = "knowledge"
    namespaces: Annotated[list[str], Field(description="Override namespaces to search.", min_length=1)]


class InsightRetrievalOverride(BaseModel):
    """
    Type-safe runtime override for insight (MongoDB) retrieval.

    Used to override which insight sources an InsightRetrievalAgent should query
    at runtime. The 'type' discriminator enables type-safe union handling.
    """

    type: Literal["insight"] = "insight"
    sources: Annotated[list[InsightSourceConfig], Field(description="Override insight sources to query.", min_length=1)]


# Discriminated union - Pydantic uses 'type' field to determine which model to use
RetrievalOverride = Annotated[
    KnowledgeRetrievalOverride | InsightRetrievalOverride,
    Field(discriminator="type"),
]
