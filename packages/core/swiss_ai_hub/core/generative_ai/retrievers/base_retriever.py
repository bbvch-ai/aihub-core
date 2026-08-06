from abc import ABC, abstractmethod

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.retrievers.base_retriever_config import BaseRetrieverConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""

    def __init__(self, config: BaseRetrieverConfig):
        self.config = config

    @abstractmethod
    async def retrieve(self, query: str, t: LocaleHandler, user: UserIdentity | None = None) -> list[IngestedNode]:
        """Retrieve nodes matching the query."""
        ...
