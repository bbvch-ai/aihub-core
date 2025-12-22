import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings

logger = logging.getLogger(__name__)


class S3AnonymousFileAccessService:
    """
    S3 implementation for generating presigned URLs for anonymous file access.

    This service provides secure, temporary access to S3 objects through presigned URLs.
    It supports both AWS S3 and SeaweedFS (S3-compatible) storage backends.

    The service uses boto3 for S3 interactions and relies on S3StorageSettings for
    connection parameters including endpoint URL, access keys, and region.

    Two S3 clients are maintained:
    - Internal client: Uses the internal endpoint for server-side operations
    - Public client: Uses the public endpoint for generating presigned URLs that
      browsers can access (e.g., via Traefik-routed domain)
    """

    def __init__(self):
        """
        Initialize the S3 anonymous file access service.

        Loads S3 configuration and creates boto3 client instances for both
        internal operations and public URL generation.
        """
        try:
            self._s3_config = S3StorageSettings()
            self._s3_client = self._create_s3_client(self._s3_config.ENDPOINT)
            self._s3_public_client = self._create_s3_client(self._s3_config.get_public_endpoint())
        except Exception as e:
            logger.error(f"Failed to initialize S3 service: {e}")
            raise

    def _create_s3_client(self, endpoint_url: str):
        """
        Create and configure an S3 client for MinIO or AWS S3.

        Uses configuration from S3StorageSettings to set up the boto3 client with
        appropriate endpoint URL, credentials, and region settings.

        Signature v4 is explicitly configured for consistent URL encoding behavior
        with presigned URLs, particularly for filenames containing spaces.
        """
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=self._s3_config.ACCESS_KEY,
            aws_secret_access_key=self._s3_config.SECRET_KEY.get_secret_value(),
            region_name=self._s3_config.REGION,
            config=Config(signature_version="s3v4"),
        )

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

    @trace_fn
    def delete_file(self, container: str, file_path: str) -> None:
        """
        Delete a file from S3/MinIO storage.

        Permanently removes the specified file from the storage bucket.
        This operation cannot be undone.
        """
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("File path cannot be empty")

        try:
            self._s3_client.delete_object(Bucket=container, Key=file_path)
            logger.debug(f"Deleted file: {container}/{file_path}")
        except ClientError as e:
            logger.error(f"Failed to delete file {container}/{file_path}: {e}")
            raise Exception(f"Failed to delete file: {e}")

    @trace_fn
    def delete_directory(self, container: str, directory_path: str) -> None:
        """
        Delete a directory and all its contents from S3/MinIO storage.

        Recursively deletes all files within the specified directory prefix.
        This operation cannot be undone.
        """
        if not container or not container.strip():
            raise ValueError("Container name cannot be empty")
        if not directory_path or not directory_path.strip():
            raise ValueError("Directory path cannot be empty")

        try:
            # Ensure path ends with / for proper prefix matching
            prefix = directory_path.rstrip("/") + "/"

            # List all objects with the prefix
            paginator = self._s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=container, Prefix=prefix)

            objects_to_delete = []
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        objects_to_delete.append({"Key": obj["Key"]})

            if objects_to_delete:
                # Delete objects in batches (S3 allows max 1000 per request)
                for i in range(0, len(objects_to_delete), 1000):
                    batch = objects_to_delete[i : i + 1000]
                    self._s3_client.delete_objects(Bucket=container, Delete={"Objects": batch})

            logger.debug(f"Deleted directory: {container}/{directory_path} ({len(objects_to_delete)} objects)")
        except ClientError as e:
            logger.error(f"Failed to delete directory {container}/{directory_path}: {e}")
            raise Exception(f"Failed to delete directory: {e}")
