from typing import Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair


class RetrievalRuntimeConfig(BaseModel):
    """A `KnowledgeRetrieverConfig` paired with per-run runtime overrides.

    Unlike `*Config` classes that inherit from `Form`, this is a plain `BaseModel` — it carries data
    that must not pollute the design-time form schema (e.g. publisher-supplied metadata filters
    injected by `narrow_retrievers`).
    """

    config: Annotated[KnowledgeRetrieverConfig, Field(description="The base retriever configuration.")]
    additional_metadata_filters: Annotated[
        list[MetadataFilterPair],
        Field(
            default_factory=list,
            description="Runtime metadata filters applied AND-wise to this retrieval.",
        ),
    ]

    @classmethod
    def from_config(cls, config: KnowledgeRetrieverConfig) -> Self:
        return cls(config=config)
