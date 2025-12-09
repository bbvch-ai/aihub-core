from aihub_lib.generative_ai.retrievers.BaseRetriever import BaseRetriever
from aihub_lib.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig, RetrieverType
from aihub_lib.generative_ai.retrievers.InsightRetriever import InsightRetriever
from aihub_lib.generative_ai.retrievers.InsightRetrieverConfig import InsightRetrieverConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetriever import KnowledgeRetriever
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import (
    KnowledgeRetrieverConfig,
    RetrieveSummariesConfig,
)

RetrieverConfig = KnowledgeRetrieverConfig | InsightRetrieverConfig


def create_retriever(config: RetrieverConfig) -> BaseRetriever:
    """Factory function to create the appropriate retriever based on config type."""
    if isinstance(config, KnowledgeRetrieverConfig):
        return KnowledgeRetriever(config)
    elif isinstance(config, InsightRetrieverConfig):
        return InsightRetriever(config)
    else:
        raise ValueError(f"Unknown retriever config type: {type(config)}")


__all__ = [
    "BaseRetriever",
    "BaseRetrieverConfig",
    "RetrieverType",
    "KnowledgeRetriever",
    "KnowledgeRetrieverConfig",
    "RetrieveSummariesConfig",
    "InsightRetriever",
    "InsightRetrieverConfig",
    "RetrieverConfig",
    "create_retriever",
]
