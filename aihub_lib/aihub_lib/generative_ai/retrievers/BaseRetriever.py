from abc import ABC, abstractmethod

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""

    def __init__(self, config: BaseRetrieverConfig):
        self.config = config

    @abstractmethod
    async def retrieve(self, query: str, t: LocaleHandler) -> list[IngestedNode]:
        """Retrieve nodes matching the query."""
        ...
