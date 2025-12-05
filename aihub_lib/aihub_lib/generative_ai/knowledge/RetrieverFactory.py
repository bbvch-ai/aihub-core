"""Factory for creating retriever instances from configuration."""

from aihub_lib.generative_ai.knowledge.BaseRetriever import BaseRetriever
from aihub_lib.generative_ai.knowledge.InsightRetriever import InsightRetriever
from aihub_lib.generative_ai.knowledge.InsightRetrieverConfig import InsightRetrieverConfig
from aihub_lib.generative_ai.knowledge.KnowledgeRetriever import KnowledgeRetriever
from aihub_lib.generative_ai.knowledge.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig

RetrieverConfig = KnowledgeRetrieverConfig | InsightRetrieverConfig


def create_retriever(config: RetrieverConfig) -> BaseRetriever:
    """
    Factory function to instantiate the correct retriever based on config type.

    Args:
        config: A retriever configuration (KnowledgeRetrieverConfig or InsightRetrieverConfig)

    Returns:
        The appropriate retriever instance

    Raises:
        ValueError: If the retriever_type is unknown
    """
    if isinstance(config, KnowledgeRetrieverConfig):
        return KnowledgeRetriever(config)
    elif isinstance(config, InsightRetrieverConfig):
        return InsightRetriever(config)
    raise ValueError(f"Unknown retriever type: {config.retriever_type}")
