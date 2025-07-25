from abc import ABC, abstractmethod


class AbstractAnonymousFileAccessService(ABC):
    """
    Abstract base class for generating temporary, secure access URLs for files.

    This interface defines the contract for anonymous file access services across
    different cloud storage backends (Azure Blob Storage, AWS S3, MinIO, etc.).

    Implementations of this class provide secure, time-limited access to stored
    files without requiring users to have direct cloud storage credentials.
    This is typically achieved through:
    - Azure: SAS (Shared Access Signature) tokens
    - S3/MinIO: Presigned URLs

    The service also provides URL signing capabilities for internal secure
    communication between application components.

    Example usage:
        ```python
        service = SomeFileAccessService()
        temp_url = service.generate_sas_url("my-container", "path/file.pdf", 2)
        # URL is valid for 2 hours
        ```
    """

    @abstractmethod
    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24) -> str:
        """
        Generate a temporary, secure URL for read-only access to a specific file.

        Creates a time-limited URL that allows anonymous access to a file stored
        in cloud storage without requiring authentication credentials. The URL
        automatically expires after the specified duration for security.

        The maximum allowed lifetime may vary by storage backend.
        Azure SAS tokens support up to 7 days, S3 presigned URLs up to 7 days.
        """
        pass

    @abstractmethod
    def get_url_signing_secret(self) -> str:
        """
        Get the secret key used for signing internal URLs and creating HMAC signatures.

        This method returns the cryptographic secret used by the FileService
        to create and verify HMAC signatures for internal URL generation.
        The secret ensures that only authorized components can generate
        valid internal file access URLs.

        This method returns sensitive cryptographic material.
        Ensure proper access controls and logging are in place.
        The secret should be kept confidential and rotated regularly.
        """
        pass
