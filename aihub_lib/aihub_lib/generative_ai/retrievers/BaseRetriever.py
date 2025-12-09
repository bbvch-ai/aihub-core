from abc import ABC, abstractmethod

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""

    def __init__(self, config: BaseRetrieverConfig):
        self.config = config

    @abstractmethod
    async def retrieve(self, query: str) -> list[IngestedNode]:
        """Retrieve nodes matching the query."""
        ...
