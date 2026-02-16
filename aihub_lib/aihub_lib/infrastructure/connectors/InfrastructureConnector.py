import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class InfrastructureConnector(ABC):
    """Base class for composable infrastructure connections that agents can opt into."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier used as the key in health check responses (e.g. 'milvus', 'mongodb')."""
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection to the infrastructure service."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down the connection cleanly."""
        ...

    @abstractmethod
    def check_health(self) -> bool:
        """Synchronous health check — called from a background thread by HealthServer."""
        ...
