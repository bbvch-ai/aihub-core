from abc import ABC, abstractmethod
from typing import Any

from dagster import ConfigurableResource, InitResourceContext


class AbstractDataLakeFileSystemResource(ConfigurableResource, ABC):
    """
    Abstract base class for data lake file system resources.
    This provides a common interface for both Azure and S3 implementations.
    """

    @abstractmethod
    def create_resource(self, context: InitResourceContext) -> Any:
        """
        Create and return the file system client.
        For Azure, this returns AzureBlobFileSystem.
        For S3, this returns S3FileSystem.
        """
        pass
