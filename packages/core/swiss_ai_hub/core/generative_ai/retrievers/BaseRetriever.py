from abc import ABC, abstractmethod

from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode
from swiss_ai_hub.core.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""

    def __init__(self, config: BaseRetrieverConfig):
        self.config = config

    @abstractmethod
    async def retrieve(self, query: str, t: LocaleHandler) -> list[IngestedNode]:
        """Retrieve nodes matching the query."""
        ...
