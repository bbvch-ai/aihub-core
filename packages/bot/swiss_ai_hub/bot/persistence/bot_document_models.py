from typing import ClassVar

from beanie import Document

from swiss_ai_hub.bot.persistence.entities.conversation_entity import ConversationEntity, ConversationTracker
from swiss_ai_hub.bot.persistence.entities.path_entity import PathEntity


class BotDocumentModels:
    """The Beanie documents only the bot owns, bound next to the core documents when the bot starts (#1966)."""

    DOCUMENT_MODELS: ClassVar[list[type[Document]]] = [ConversationEntity, ConversationTracker, PathEntity]
