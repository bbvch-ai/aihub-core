from typing import ClassVar

from beanie import Document, init_beanie
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.notification.notification_entity import NotificationEntity


class BeanieInitializer:
    """The entities already ported from MongoEngine to Beanie (#1634), and how a process starts them.

    The client is bound to the event loop it is created on, so a process creates it inside its running loop, and
    `init_beanie` binds every listed document to it. MongoEngine keeps serving every entity not listed here.
    """

    DOCUMENT_MODELS: ClassVar[list[type[Document]]] = [AgentConfigEntityDocument, NotificationEntity]

    @staticmethod
    def create_client() -> AsyncMongoClient:
        return AsyncMongoClient(MongoSettings().CONNECTION_STRING.get_secret_value(), uuidRepresentation="standard")

    @staticmethod
    async def initialize(client: AsyncMongoClient) -> None:
        await init_beanie(
            database=client[AIHubSettings().MONGO_MAIN_DB_NAME],
            document_models=BeanieInitializer.DOCUMENT_MODELS,
        )
