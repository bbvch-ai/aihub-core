import boto3
from botocore.exceptions import ClientError

from aihub_lib.generative_ai.document.accessor.AbstractAnonymousFileAccessService import (
    AbstractAnonymousFileAccessService,
)
from aihub_lib.infrastructure.s3.S3Config import S3Config


class S3AnonymousFileAccessService(AbstractAnonymousFileAccessService):
    """S3/MinIO-specific implementation for generating presigned URLs for object access."""

    def __init__(self):
        self._s3_config = S3Config()
        self._s3_client = self._create_s3_client()

    def _create_s3_client(self):
        """Creates an S3 client configured for MinIO or AWS S3."""
        return boto3.client(
            "s3",
            endpoint_url=self._s3_config.ENDPOINT_URL,
            aws_access_key_id=self._s3_config.ACCESS_KEY,
            aws_secret_access_key=self._s3_config.SECRET_KEY,
            region_name=self._s3_config.REGION,
        )

    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24) -> str:
        """Generates a presigned URL for temporary read-only access to an S3 object."""
        try:
            # Generate presigned URL for GET operation
            presigned_url = self._s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": container, "Key": file_path},
                ExpiresIn=int(lifetime_hours * 3600),  # Convert hours to seconds
            )
            return presigned_url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    def get_url_signing_secret(self) -> str:
        """
        Gets the URL signing secret for S3/MinIO.
        Uses the SECRET_KEY from S3Config as the signing secret.
        """
        # For S3/MinIO, we'll use the secret access key as the signing secret
        # In production, you might want to use a separate dedicated secret
        return self._s3_config.SECRET_KEY
