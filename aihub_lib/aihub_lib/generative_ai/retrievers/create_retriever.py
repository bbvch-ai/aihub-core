from aihub_lib.generative_ai.retrievers import (
    BaseRetriever,
    BaseRetrieverConfig,
    InsightRetriever,
    InsightRetrieverConfig,
    KnowledgeRetriever,
    KnowledgeRetrieverConfig,
)


def create_retriever(config: BaseRetrieverConfig) -> BaseRetriever:
    """Factory function to create the appropriate retriever based on config type."""
    if isinstance(config, KnowledgeRetrieverConfig):
        return KnowledgeRetriever(config)
    elif isinstance(config, InsightRetrieverConfig):
        return InsightRetriever(config)
    else:
        raise ValueError(f"Unknown retriever config type: {type(config)}")
