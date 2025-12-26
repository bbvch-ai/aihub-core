import logging
from typing import TYPE_CHECKING, Any

from botocore.exceptions import ClientError

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)


class S3AnonymousFileAccessService:
    """
    S3 implementation for generating presigned URLs for anonymous file access.

    This service provides secure, temporary access to S3 objects through presigned URLs.
    It supports both AWS S3 and SeaweedFS (S3-compatible) storage backends.

    The service uses boto3 for S3 interactions and accepts pre-configured clients
    for dependency injection, enabling connection reuse and proper health checking.

    Two S3 clients are maintained:
    - Internal client: Uses the internal endpoint for server-side operations
    - Public client: Uses the public endpoint for generating presigned URLs that
      browsers can access (e.g., via Traefik-routed domain)
    """

    def __init__(
        self,
        s3_client: "S3Client | Any",
        s3_public_client: "S3Client | Any",
        s3_settings: S3StorageSettings,
    ):
        """
        Initialize the S3 anonymous file access service with injected clients.

        Accepts pre-configured boto3 clients for both internal operations and
        public URL generation, enabling proper dependency injection.
        """
        self._s3_client = s3_client
        self._s3_public_client = s3_public_client
        self._s3_config = s3_settings

    @trace_fn
    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24) -> str:
        """
        Generate a presigned URL for temporary read-only access to an S3 object.

        Creates a time-limited URL that allows anonymous access to a specific
        S3 object without requiring AWS credentials. The URL expires after
        the specified lifetime.

        The URL is generated using the public endpoint so it can be accessed
        by browsers (e.g., via Traefik-routed domain instead of internal Docker DNS).

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
            # Generate presigned URL for GET operation using the public client
            # so the URL is accessible from browsers
            presigned_url = self._s3_public_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": container, "Key": file_path},
                ExpiresIn=int(lifetime_hours * 3600),  # Convert hours to seconds
            )
            logger.debug(f"Generated presigned URL for {container}/{file_path}, expires in {lifetime_hours}h")
            return presigned_url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {e}")

    @trace_fn
    def get_url_signing_secret(self) -> str:
        """
        Get the URL signing secret for S3/MinIO operations.

        Returns the secret access key from S3StorageSettings, which is used as the
        signing secret for generating secure URLs and request signatures.
        """
        return self._s3_config.URL_SIGNING_SECRET.get_secret_value()

    def generate_upload_url(self, container: str, file_path: str, content_type: str, lifetime_hours: int = 1) -> str:
        """
        Generate a presigned URL for uploading a file to S3/MinIO.

        Creates a time-limited URL that allows anonymous upload to a specific
        S3 object path without requiring AWS credentials. The URL expires after
        the specified lifetime.

        The URL is generated using the public endpoint so it can be accessed
        by browsers (e.g., via Traefik-routed domain instead of internal Docker DNS).
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

        try:
            # Generate presigned URL for PUT operation using the public client
            # so the URL is accessible from browsers
            presigned_url = self._s3_public_client.generate_presigned_url(
                "put_object",
                Params={"Bucket": container, "Key": file_path, "ContentType": content_type},
                ExpiresIn=int(lifetime_hours * 3600),  # Convert hours to seconds
            )
            logger.debug(f"Generated presigned upload URL for {container}/{file_path}, expires in {lifetime_hours}h")
            return presigned_url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned upload URL: {e}")

    def verify_file_exists(self, container: str, file_path: str) -> bool:
        """
        Verify that a file exists in S3/MinIO storage.

        This method checks if a file was successfully uploaded by attempting
        to retrieve its metadata. This is more efficient than downloading
        the entire file just to verify existence.
        """
        # Validate input parameters
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")

        try:
            # Use head_object to check existence without downloading the file
            self._s3_client.head_object(Bucket=container, Key=file_path)
            logger.debug(f"File verification successful: {container}/{file_path}")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ["404", "NoSuchKey"]:
                # File doesn't exist - this is expected behavior, not an error
                logger.debug(f"File does not exist: {container}/{file_path}")
                return False
            else:
                # Unexpected error occurred
                logger.error(f"Failed to verify file existence {container}/{file_path}: {e}")
                raise Exception(f"Failed to verify file existence: {e}")
        except Exception as e:
            logger.error(f"Failed to verify file existence {container}/{file_path}: {e}")
            raise Exception(f"Failed to verify file existence: {e}")

    def list_files(self, container: str, prefix: str = "") -> list[dict]:
        """
        List files in S3/MinIO storage with optional prefix filtering.

        This method retrieves a list of objects in the specified bucket
        that match the given prefix. It's useful for browsing and discovering files
        in S3/MinIO storage.
        """
        # Validate input parameters
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")

        try:
            files = []
            paginator = self._s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=container,
                Prefix=prefix,
            )

            for page in page_iterator:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    # Skip directories (keys ending with '/')
                    if obj["Key"].endswith("/"):
                        continue

                    files.append(
                        {
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": obj["LastModified"].isoformat(),
                            "etag": obj.get("ETag", "").strip('"'),
                        }
                    )

            logger.debug(f"Listed {len(files)} files in {container} with prefix '{prefix}'")
            return files

        except ClientError as e:
            logger.error(f"Failed to list files in {container} with prefix '{prefix}': {e}")
            raise Exception(f"Failed to list files: {e}")
        except Exception as e:
            logger.error(f"Failed to list files in {container} with prefix '{prefix}': {e}")
            raise Exception(f"Failed to list files: {e}")
