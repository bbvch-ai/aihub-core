import logging

from pymilvus import MilvusClient

from aihub_lib.infrastructure.connectors.InfrastructureConnector import InfrastructureConnector
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.routes.health.health_checks import check_milvus

logger = logging.getLogger(__name__)


class MilvusConnector(InfrastructureConnector):
    """Connects to Milvus for vector-database health checks."""

    def __init__(self) -> None:
        self.client: MilvusClient | None = None

    @property
    def name(self) -> str:
        return "milvus"

    async def connect(self) -> None:
        settings = MilvusSettings()
        self.client = MilvusClient(uri=settings.URL, token=settings.get_token())
        logger.debug("Connected to Milvus")

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
        logger.debug("Disconnected from Milvus")

    def check_health(self) -> bool:
        return check_milvus(self.client)
