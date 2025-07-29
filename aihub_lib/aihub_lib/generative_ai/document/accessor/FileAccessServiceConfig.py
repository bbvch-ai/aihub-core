from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aihub_lib.generative_ai.document.accessor.AbstractAnonymousFileAccessService import (
    AbstractAnonymousFileAccessService,
)
from aihub_lib.generative_ai.document.accessor.AzureAnonymousFileAccessService import (
    AzureAnonymousFileAccessService,
)
from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import (
    S3AnonymousFileAccessService,
)


class FileAccessServiceConfig(BaseSettings):
    """
    Global configuration for anonymous file access service using Pydantic BaseSettings.

    This configuration class provides a centralized way to select and configure
    the appropriate file access service backend (Azure, S3, or MinIO). It uses
    environment variables for configuration and provides a factory method to
    instantiate the correct service implementation.

    The configuration supports multiple storage backends:
    - azure: Microsoft Azure Blob Storage
    - s3: Amazon S3
    - minio: MinIO (S3-compatible object storage)

    Example:
        ```python
        # Set environment variable
        os.environ["STORAGE_BACKEND"] = "s3"

        # Use in code
        config = FileAccessServiceConfig()
        service = config.service  # Returns S3AnonymousFileAccessService
        url = service.generate_sas_url("my-bucket", "path/to/file.pdf")
        ```
    """

    STORAGE_BACKEND: Literal["azure", "s3", "minio"] = Field(default="minio", description="Storage backend to use")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def service(self) -> AbstractAnonymousFileAccessService:
        """
        Get the configured anonymous file access service instance.

        This factory method returns the appropriate service implementation
        based on the configured STORAGE_BACKEND setting.

        This property creates a new service instance on each access.
        Consider caching the result if called frequently.
        """
        if self.STORAGE_BACKEND == "azure":
            return AzureAnonymousFileAccessService()
        elif self.STORAGE_BACKEND in ["s3", "minio"]:
            return S3AnonymousFileAccessService()
        else:
            raise ValueError(f"Unknown storage backend: {self.STORAGE_BACKEND}")
