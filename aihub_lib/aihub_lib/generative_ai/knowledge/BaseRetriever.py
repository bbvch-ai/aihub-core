"""Abstract base class for knowledge retrieval."""

from abc import ABC, abstractmethod

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.knowledge.BaseRetrieverConfig import BaseRetrieverConfig


class BaseRetriever(ABC):
    """
    Abstract base class for knowledge retrieval.

    Implementations can retrieve from different sources:
    - KnowledgeRetriever: Vector store (Milvus) semantic search
    - InsightRetriever: MongoDB text search on expert insights

    All implementations return a consistent list[IngestedNode] format
    for uniform processing in the RAGAgent workflow.
    """

    def __init__(self, config: BaseRetrieverConfig) -> None:
        self._base_config = config

    @abstractmethod
    async def retrieve(self, query: str) -> list[IngestedNode]:
        """
        Retrieve relevant nodes for the given query.

        Args:
            query: The search query string

        Returns:
            List of IngestedNode objects containing retrieved content
        """

    @property
    def name(self) -> str:
        """Human-readable name for this retriever."""
        return self._base_config.name

    @property
    def is_enabled(self) -> bool:
        """Whether this retriever is active."""
        return self._base_config.enabled
