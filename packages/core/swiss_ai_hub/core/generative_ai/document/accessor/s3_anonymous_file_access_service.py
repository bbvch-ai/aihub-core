import logging

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.infrastructure.s3.s3_storage_settings import S3StorageSettings

logger = logging.getLogger(__name__)

_CONTAINER_NAME_EMPTY_ERROR = "Container name cannot be empty"
_FILE_PATH_EMPTY_ERROR = "File path cannot be empty"


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
        s3_client: S3Client,
        s3_public_client: S3Client,
        s3_settings: S3StorageSettings,
        s3_internal_client: S3Client | None = None,
    ):
        """
        Initialize the S3 anonymous file access service with injected clients.

        Accepts pre-configured boto3 clients for internal operations, public URL
        generation, and (optionally) in-cluster presigned URL signing, enabling proper
        dependency injection. `s3_internal_client` signs URLs that another in-cluster
        service fetches (e.g. the LiteLLM gateway); it falls back to `s3_client` when
        not provided, as browser-facing callers never sign internal URLs.
        """
        self._s3_client = s3_client
        self._s3_public_client = s3_public_client
        self._s3_internal_client = s3_internal_client or s3_client
        self._s3_config = s3_settings

    @trace_fn
    def container_exists(self, container: str) -> bool:
        """Whether the S3 container exists, independent of whether any ``BucketEntity`` row references it.

        Lets callers distinguish "free name" from "name already taken by storage we did not create" —
        platform buckets (``dagster``, ``milvus``, ``langfuse``, …) have no bucket row, so an entity-only
        duplicate check would happily bind a knowledge database onto one of them.
        """
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)

        try:
            self._s3_client.head_bucket(Bucket=container)
        except ClientError as error:
            if error.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                return False
            raise
        return True

    @trace_fn
    def ensure_bucket_with_cors(self, container: str) -> None:
        """Idempotently create the bucket and apply browser-upload CORS rules.

        Self-service knowledge databases are provisioned here at creation time: the static
        ``init-buckets.sh`` only covers the built-in buckets, so without this a presigned browser
        upload to a freshly created bucket fails its CORS preflight (the bucket has no CORS, or does
        not exist yet because the pipeline only creates it lazily on first ingest).
        """
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)

        try:
            self._s3_client.head_bucket(Bucket=container)
        except ClientError as error:
            if error.response["Error"]["Code"] not in ("404", "NoSuchBucket"):
                raise
            self._s3_client.create_bucket(Bucket=container)
            logger.info(f"Created S3 bucket '{container}' for self-service knowledge database")

        # AllowedOrigins is "*" by design: the entitlement lives in the short-lived, signed presigned URL,
        # not in CORS. The origin we would otherwise pin is the browser app's own domain (Admin UI /
        # OpenWebUI), which is deployment-specific and not known to these S3 settings — PUBLIC_ENDPOINT is
        # the S3 host, not the frontend host. Narrow this to the frontend origin only once it is configurable.
        self._s3_client.put_bucket_cors(
            Bucket=container,
            CORSConfiguration={
                "CORSRules": [
                    {
                        "AllowedHeaders": [
                            "Content-Type",
                            "x-amz-date",
                            "authorization",
                            "x-amz-security-token",
                            "x-amz-content-sha256",
                        ],
                        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
                        "AllowedOrigins": ["*"],
                        "ExposeHeaders": ["ETag", "x-amz-request-id", "x-amz-id-2", "x-amz-server-side-encryption"],
                        "MaxAgeSeconds": 3000,
                    }
                ]
            },
        )

    @trace_fn
    def generate_sas_url(self, container: str, file_path: str, lifetime_hours: int = 24, internal: bool = False) -> str:
        """
        Generate a presigned URL for temporary read-only access to an S3 object.

        Creates a time-limited URL that allows anonymous access to a specific
        S3 object without requiring AWS credentials. The URL expires after
        the specified lifetime.

        By default the URL is signed against the public endpoint so browsers can
        reach it (e.g., via Traefik-routed domain). Presigned URLs are host-bound,
        so `internal=True` signs against the in-cluster endpoint instead — needed when
        an in-cluster consumer (e.g. the LiteLLM gateway) must fetch the object over
        Docker DNS rather than the public domain. Signing is offline, so this works from
        the host even when the in-cluster host is not resolvable there.

        The maximum lifetime for presigned URLs is 7 days (168 hours).
        """
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)
        if not file_path or not file_path.strip():
            raise ValueError(_FILE_PATH_EMPTY_ERROR)
        if lifetime_hours <= 0 or lifetime_hours > 168:  # 7 days max
            raise ValueError("Lifetime must be between 1 and 168 hours")

        signing_client = self._s3_internal_client if internal else self._s3_public_client
        presigned_url = signing_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": container, "Key": file_path},
            ExpiresIn=int(lifetime_hours * 3600),
        )
        logger.debug(f"Generated presigned URL for {container}/{file_path}, expires in {lifetime_hours}h")
        return presigned_url

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
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)
        if not file_path or not file_path.strip():
            raise ValueError(_FILE_PATH_EMPTY_ERROR)
        if not content_type or not content_type.strip():
            raise ValueError("Content type cannot be empty")
        if lifetime_hours <= 0 or lifetime_hours > 24:  # 24 hours max for uploads
            raise ValueError("Lifetime must be between 1 and 24 hours")

        presigned_url = self._s3_public_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": container, "Key": file_path, "ContentType": content_type},
            ExpiresIn=int(lifetime_hours * 3600),
        )
        logger.debug(f"Generated presigned upload URL for {container}/{file_path}, expires in {lifetime_hours}h")
        return presigned_url

    @trace_fn
    def download_file(self, container: str, file_path: str) -> bytes:
        """Raw byte download for in-memory processing (e.g. zip extraction, parsing)."""
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)
        if not file_path or not file_path.strip():
            raise ValueError(_FILE_PATH_EMPTY_ERROR)

        response = self._s3_client.get_object(Bucket=container, Key=file_path)
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def verify_file_exists(self, container: str, file_path: str) -> bool:
        """
        Verify that a file exists in S3/MinIO storage.

        This method checks if a file was successfully uploaded by attempting
        to retrieve its metadata. This is more efficient than downloading
        the entire file just to verify existence.
        """
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)
        if not file_path or not file_path.strip():
            raise ValueError(_FILE_PATH_EMPTY_ERROR)

        try:
            self._s3_client.head_object(Bucket=container, Key=file_path)
            logger.debug(f"File verification successful: {container}/{file_path}")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ["404", "NoSuchKey"]:
                # A missing object is the expected negative result, not a failure.
                logger.debug(f"File does not exist: {container}/{file_path}")
                return False
            raise

    def list_files(self, container: str, prefix: str = "") -> list[dict]:
        """
        List files in S3/MinIO storage with optional prefix filtering.

        This method retrieves a list of objects in the specified bucket
        that match the given prefix. It's useful for browsing and discovering files
        in S3/MinIO storage.
        """
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)

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

    @trace_fn
    def delete_file(self, container: str, file_path: str) -> None:
        """Permanently remove a single object from S3/MinIO storage."""
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)
        if not file_path or not file_path.strip():
            raise ValueError(_FILE_PATH_EMPTY_ERROR)

        self._s3_client.delete_object(Bucket=container, Key=file_path)
        logger.info(f"Deleted file: {container}/{file_path}")

    @trace_fn
    def delete_container(self, container: str) -> None:
        """Empty and remove an S3 container, tolerating one that is already gone.

        S3 refuses to delete a non-empty bucket, so every object is removed first (paginated, in
        1000-key batches). Idempotent: a missing bucket is treated as success, so this is safe to call
        as a create-time rollback and as a repeatable knowledge-database teardown step.
        """
        if not container or not container.strip():
            raise ValueError(_CONTAINER_NAME_EMPTY_ERROR)

        try:
            paginator = self._s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=container):
                keys = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
                if keys:
                    self._s3_client.delete_objects(Bucket=container, Delete={"Objects": keys})

            self._s3_client.delete_bucket(Bucket=container)
            logger.info(f"Deleted S3 container '{container}'")
        except ClientError as error:
            if error.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                return
            raise
