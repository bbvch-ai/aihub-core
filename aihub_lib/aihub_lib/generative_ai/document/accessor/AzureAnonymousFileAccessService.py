import logging
from datetime import UTC, datetime, timedelta

from azure.storage.blob import BlobSasPermissions, generate_blob_sas

from aihub_lib.generative_ai.document.accessor.AbstractAnonymousFileAccessService import (
    AbstractAnonymousFileAccessService,
)
from aihub_lib.infrastructure.azure.blob_storage.BlobStorageAccess import BlobStorageAccess

logger = logging.getLogger(__name__)


class AzureAnonymousFileAccessService(AbstractAnonymousFileAccessService):
    """Azure-specific implementation for generating temporary SAS URLs for blob access."""

    def __init__(self):
        self._blob_storage_access = BlobStorageAccess()

    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24) -> str:
        """Generates a temporary read-only SAS URL for a specific blob."""
        account_name = self._blob_storage_access.get_account_name()
        service_endpoint = self._blob_storage_access.get_service_endpoint()
        blob_service_client = self._blob_storage_access.get_blob_service_client()

        delegation_key_start_time = datetime.now(UTC)
        delegation_key_expiry_time = delegation_key_start_time + timedelta(hours=lifetime_hours)

        user_delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=delegation_key_start_time, key_expiry_time=delegation_key_expiry_time
        )

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=file_path,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(UTC) + timedelta(hours=lifetime_hours),
        )

        return f"{service_endpoint}/{container}/{file_path}?{sas_token}"

    def get_url_signing_secret(self) -> str:
        """Gets the URL signing secret from Azure Blob Storage configuration."""
        return self._blob_storage_access.get_url_signing_secret()

    def generate_upload_url(self, container: str, file_path: str, content_type: str, lifetime_hours: int = 1) -> str:
        """
        Generate a presigned URL for uploading a file to Azure Blob Storage.

        Creates a time-limited SAS URL that allows anonymous upload to a specific
        blob without requiring Azure credentials. The URL expires after the
        specified lifetime.
        """
        # Validate input parameters
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")
        if not content_type or not content_type.strip():
            raise ValueError("Content type cannot be empty")
        if lifetime_hours <= 0 or lifetime_hours > 24:  # 24 hours max for uploads
            raise ValueError("Lifetime must be between 1 and 24 hours")

        account_name = self._blob_storage_access.get_account_name()
        service_endpoint = self._blob_storage_access.get_service_endpoint()
        blob_service_client = self._blob_storage_access.get_blob_service_client()

        delegation_key_start_time = datetime.now(UTC)
        delegation_key_expiry_time = delegation_key_start_time + timedelta(hours=lifetime_hours)

        user_delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=delegation_key_start_time, key_expiry_time=delegation_key_expiry_time
        )

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=file_path,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(write=True, create=True),  # Upload permissions
            expiry=datetime.now(UTC) + timedelta(hours=lifetime_hours),
        )

        return f"{service_endpoint}/{container}/{file_path}?{sas_token}"

    def verify_file_exists(self, container: str, file_path: str) -> bool:
        """
        Verify that a file exists in Azure Blob Storage.

        This method checks if a file was successfully uploaded by attempting
        to retrieve its properties. This is more efficient than downloading
        the entire file just to verify existence.
        """
        # Validate input parameters
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")

        try:
            blob_service_client = self._blob_storage_access.get_blob_service_client()
            blob_client = blob_service_client.get_blob_client(container=container, blob=file_path)

            # Use exists() method which is efficient and doesn't download the blob
            exists = blob_client.exists()
            if exists:
                logger.debug(f"File verification successful: {container}/{file_path}")
            else:
                logger.debug(f"File does not exist: {container}/{file_path}")

            return exists
        except Exception as e:
            logger.error(f"Failed to verify file existence {container}/{file_path}: {e}")
            raise Exception(f"Failed to verify file existence: {e}")

    def list_files(self, container: str, prefix: str = "") -> list[dict]:
        """
        List files in Azure Blob Storage with optional prefix filtering.

        This method retrieves a list of blobs in the specified container
        that match the given prefix. It's useful for browsing and discovering files
        in Azure Blob Storage.
        """
        # Validate input parameters
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")

        try:
            blob_service_client = self._blob_storage_access.get_blob_service_client()
            container_client = blob_service_client.get_container_client(container)

            files = []
            blob_list = container_client.list_blobs(name_starts_with=prefix)

            for blob in blob_list:
                # Skip directories (blobs ending with '/')
                if blob.name.endswith("/"):
                    continue

                files.append(
                    {
                        "key": blob.name,
                        "size": blob.size,
                        "last_modified": blob.last_modified.isoformat() if blob.last_modified else "",
                        "etag": blob.etag.strip('"') if blob.etag else "",
                    }
                )

            logger.debug(f"Listed {len(files)} files in {container} with prefix '{prefix}'")
            return files

        except Exception as e:
            logger.error(f"Failed to list files in {container} with prefix '{prefix}': {e}")
            raise Exception(f"Failed to list files: {e}")
