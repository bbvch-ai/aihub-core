import logging

from mongoengine import connect, disconnect
from mongoengine.connection import get_connection

from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.connectors.InfrastructureConnector import InfrastructureConnector
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.routes.health.health_checks import check_mongodb

logger = logging.getLogger(__name__)


class MongoConnector(InfrastructureConnector):
    """Connects to MongoDB via MongoEngine for persistence and health checks."""

    @property
    def name(self) -> str:
        return "mongodb"

    async def connect(self) -> None:
        try:
            get_connection()
            logger.debug("MongoDB already connected, skipping")
        except Exception:
            connect(
                db=AIHubSettings().MONGO_MAIN_DB_NAME,
                host=MongoSettings().CONNECTION_STRING.get_secret_value(),
                uuidRepresentation="standard",
            )
            logger.debug("Connected to MongoDB")

    async def disconnect(self) -> None:
        disconnect()
        logger.debug("Disconnected from MongoDB")

    def check_health(self) -> bool:
        return check_mongodb()
