from abc import ABC, abstractmethod
from typing import Any

from dagster import ConfigurableResource, InitResourceContext


class AbstractDataLakeClientResource(ConfigurableResource, ABC):
    """
    Abstract base class for data lake client resources.
    This provides a common interface for both Azure and S3 implementations.
    """

    container_name: str

    @abstractmethod
    def create_resource(self, context: InitResourceContext) -> Any:
        """
        Create and return the storage client.
        For Azure, this returns FileSystemClient.
        For S3, this returns boto3 S3 client.
        """
        pass
