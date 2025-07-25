from abc import ABC, abstractmethod


class AbstractAnonymousFileAccessService(ABC):
    """
    Abstract base class for generating temporary, secure access URLs for files
    stored in different cloud storage services (Azure Blob Storage, S3, MinIO, etc).
    """

    @abstractmethod
    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24) -> str:
        """
        Generates a temporary read-only URL for accessing a specific file.

        Args:
            container: Container/bucket name where the file is stored
            file_path: Path to the file within the container
            lifetime_hours: How long the URL should remain valid (default: 24 hours)

        Returns:
            A temporary URL that provides read-only access to the file
        """
        pass

    @abstractmethod
    def get_url_signing_secret(self) -> str:
        """
        Gets the secret key used for signing internal URLs.
        This is used for creating the HMAC signature in FileService.

        Returns:
            The secret key for URL signing
        """
        pass
