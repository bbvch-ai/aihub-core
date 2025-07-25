"""
Example configuration for FileService.
This should be done at application startup based on your deployment environment.
"""

import os

from aihub_api.routes.file.FileService import FileService


def configure_file_service():
    """
    Configure FileService with the appropriate anonymous file access service
    based on the deployment environment.
    """
    # Get storage backend from environment variable
    storage_backend = os.getenv("STORAGE_BACKEND", "azure").lower()

    if storage_backend == "azure":
        from aihub_lib.generative_ai.document.accessor.AzureAnonymousFileAccessService import (
            AzureAnonymousFileAccessService,
        )

        FileService.anonymous_file_access_service = AzureAnonymousFileAccessService()
    elif storage_backend == "s3" or storage_backend == "minio":
        from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import (
            S3AnonymousFileAccessService,
        )

        FileService.anonymous_file_access_service = S3AnonymousFileAccessService()
    else:
        raise ValueError(f"Unknown storage backend: {storage_backend}")

    print(f"FileService configured with {storage_backend} backend")
