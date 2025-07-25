from abc import ABC, abstractmethod

from aihub_pipeline.types.DataLakeFile import DataLakeFile


class AbstractDataLakeClient(ABC):
    """
    Abstract interface for data lake clients that provides cloud-agnostic methods.
    This wraps the underlying cloud-specific clients (Azure FileSystemClient, boto3 S3 client)
    and provides a unified interface.
    """

    def __init__(self, container_name: str):
        self.container_name = container_name

    @abstractmethod
    def get_all_files(
        self,
        directory_name: str,
        figures_directory_name: str,
    ) -> list[DataLakeFile]:
        """Get all files in the specified directory, excluding figures directory."""
        pass

    @abstractmethod
    def get_file_metadata(self, file_path: str) -> dict:
        """Get metadata for a specific file."""
        pass

    @abstractmethod
    def directory_exists(self, directory_path: str) -> bool:
        """Check if a directory exists."""
        pass

    @abstractmethod
    def list_directory_contents(self, directory_path: str) -> list[str]:
        """List contents of a directory."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """Delete a file."""
        pass

    @abstractmethod
    def delete_directory(self, directory_path: str) -> None:
        """Delete a directory and all its contents."""
        pass
