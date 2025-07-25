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
    This allows utility functions in aihub_lib to access the configured service.
    """

    STORAGE_BACKEND: Literal["azure", "s3", "minio"] = Field(default="azure", description="Storage backend to use")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def service(self) -> AbstractAnonymousFileAccessService:
        """Get the configured anonymous file access service."""
        if self.STORAGE_BACKEND == "azure":
            return AzureAnonymousFileAccessService()
        elif self.STORAGE_BACKEND in ["s3", "minio"]:
            return S3AnonymousFileAccessService()
        else:
            raise ValueError(f"Unknown storage backend: {self.STORAGE_BACKEND}")
