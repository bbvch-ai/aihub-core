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
        """
        Get all files in the specified directory, excluding figures directory.

        Args:
            directory_name: The directory to search in
            figures_directory_name: Directory name to exclude from results

        Returns:
            List of DataLakeFile objects
        """
        pass

    @abstractmethod
    def get_file_metadata(self, file_path: str) -> dict:
        """
        Get metadata for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary of metadata
        """
        pass
