import logging

import boto3
from botocore.exceptions import ClientError

from aihub_lib.generative_ai.document.accessor.AbstractAnonymousFileAccessService import (
    AbstractAnonymousFileAccessService,
)
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings

logger = logging.getLogger(__name__)


class S3AnonymousFileAccessService(AbstractAnonymousFileAccessService):
    """
    S3/MinIO-specific implementation for generating presigned URLs for anonymous file access.

    This service provides secure, temporary access to S3 objects through presigned URLs.
    It supports both AWS S3 and MinIO (S3-compatible) storage backends.

    The service uses boto3 for S3 interactions and relies on S3StorageSettings for
    connection parameters including endpoint URL, access keys, and region.
    """

    def __init__(self):
        """
        Initialize the S3 anonymous file access service.

        Loads S3 configuration and creates a boto3 client instance.
        """
        try:
            self._s3_config = S3StorageSettings()
            self._s3_client = self._create_s3_client()
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            raise

    def _create_s3_client(self):
        """
        Create and configure an S3 client for MinIO or AWS S3.

        Uses configuration from S3StorageSettings to set up the boto3 client with
        appropriate endpoint URL, credentials, and region settings.
        """
        return boto3.client(
            "s3",
            endpoint_url=self._s3_config.ENDPOINT,
            aws_access_key_id=self._s3_config.ACCESS_KEY,
            aws_secret_access_key=self._s3_config.SECRET_KEY.get_secret_value(),
            region_name=self._s3_config.REGION,
        )

    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24) -> str:
        """
        Generate a presigned URL for temporary read-only access to an S3 object.

        Creates a time-limited URL that allows anonymous access to a specific
        S3 object without requiring AWS credentials. The URL expires after
        the specified lifetime.

        The maximum lifetime for presigned URLs is 7 days (168 hours).
        """
        # Validate input parameters
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")
        if lifetime_hours <= 0 or lifetime_hours > 168:  # 7 days max
            raise ValueError("Lifetime must be between 1 and 168 hours")

        try:
            # Generate presigned URL for GET operation
            presigned_url = self._s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": container, "Key": file_path},
                ExpiresIn=int(lifetime_hours * 3600),  # Convert hours to seconds
            )
            logger.debug(f"Generated presigned URL for {container}/{file_path}, expires in {lifetime_hours}h")
            return presigned_url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def get_url_signing_secret(self) -> str:
        """
        Get the URL signing secret for S3/MinIO operations.

        Returns the secret access key from S3StorageSettings, which is used as the
        signing secret for generating secure URLs and request signatures.
        """
        return self._s3_config.SECRET_KEY
