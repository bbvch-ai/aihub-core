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

    @abstractmethod
    def directory_exists(self, directory_path: str) -> bool:
        """
        Check if a directory exists.

        Args:
            directory_path: Path to the directory

        Returns:
            True if directory exists, False otherwise
        """
        pass

    @abstractmethod
    def list_directory_contents(self, directory_path: str) -> list[str]:
        """
        List contents of a directory.

        Args:
            directory_path: Path to the directory

        Returns:
            List of file/directory paths
        """
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file.

        Args:
            file_path: Path to the file to delete
        """
        pass

    @abstractmethod
    def delete_directory(self, directory_path: str) -> None:
        """
        Delete a directory and all its contents.

        Args:
            directory_path: Path to the directory to delete
        """
        pass
