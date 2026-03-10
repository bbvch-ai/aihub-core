from abc import ABC, abstractmethod

from swiss_ai_hub.pipeline.types.DataLakeFile import DataLakeFile


class AbstractDataLakeClient(ABC):
    """
    Abstract interface for data lake clients providing cloud-agnostic file operations.

    This class defines a unified interface for interacting with different cloud
    data lake services (Azure Data Lake Storage, AWS S3, MinIO) without exposing
    the underlying implementation details. It wraps cloud-specific clients and
    provides consistent method signatures across all backends.

    The interface supports common data lake operations including:
    - File discovery and metadata retrieval
    - Directory management and existence checks
    - File and directory deletion operations
    - Batch file operations with pagination

    Concrete implementations should handle:
    - Cloud-specific authentication and configuration
    - Error handling and retry logic
    - Performance optimization for large datasets
    - Proper resource cleanup and connection management

    Example:
        ```python
        # Azure implementation
        azure_client = AzureDataLakeClient("my-container", azure_fs_client)

        # S3 implementation
        s3_client = S3DataLakeClient("my-bucket", boto3_s3_client)

        # Both provide the same interface
        files = client.get_all_files("documents", "figures")
        ```
    """

    def __init__(self, container_name: str):
        self.container_name = container_name

    @abstractmethod
    def build_uri(self, file_path: str) -> str:
        """
        Build a complete URI for a file path in this data lake.

        This method constructs a URI using the same format that get_all_files()
        returns, ensuring consistency across URI construction and comparison.
        """
        pass

    @abstractmethod
    def _extract_storage_key(self, uri: str) -> str:
        """
        Extract the storage key from a data lake URI.

        Converts a full data lake URI to a storage-relative key by removing
        the protocol and container/bucket prefix. This is an internal method
        used to normalize URIs for backend storage operations.
        """
        pass

    @abstractmethod
    def get_all_files(self) -> list[DataLakeFile]:
        """
        Retrieve all files from a directory, excluding figures subdirectory.

        Recursively searches the specified directory for files, filtering out
        any files located within the figures directory. This is commonly used
        for document processing pipelines where figures are handled separately.

        Implementation should handle pagination for large directories
        and provide appropriate error handling for access issues.
        """
        pass

    @abstractmethod
    def get_file_metadata(self, file_path: str) -> dict:
        """
        Retrieve metadata for a specific file.

        Fetches cloud-specific metadata associated with a file, which may
        include content type, last modified time, size, custom tags, etc.
        """
        pass

    @abstractmethod
    def directory_exists(self, directory_path: str) -> bool:
        """
        Check whether a directory exists in the data lake.

        Note that directory semantics vary by storage backend:
        - Azure: True directories with metadata
        - S3/MinIO: Virtual directories (prefixes with objects)
        """
        pass

    @abstractmethod
    def list_directory_contents(self, directory_path: str) -> list[str]:
        """
        List all files and subdirectories within a directory.

        Returns a flat list of paths for both files and subdirectories
        at the specified directory level (non-recursive).
        """
        pass

    @abstractmethod
    def delete_file(self, uri: str) -> None:
        """
        Delete a specific file from the data lake using its URI.

        Permanently removes the file from storage. This operation
        cannot be undone, so implementations should consider adding
        safety checks or logging.

        This operation is irreversible. Ensure proper authorization
        and backup procedures are in place before deletion.
        """
        pass

    @abstractmethod
    def delete_directory(self, directory_path: str) -> None:
        """
        Delete a directory and all its contents recursively.

        Removes the directory and all files/subdirectories within it.
        For cloud storage with virtual directories (like S3), this deletes
        all objects with the specified prefix.

        This operation recursively deletes all contents and is irreversible.
        Implementations should provide batch operations for efficiency
        and proper error handling for partial failures.
        """
        pass
