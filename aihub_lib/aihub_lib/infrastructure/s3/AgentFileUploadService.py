import logging
import re
import uuid

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings

logger = logging.getLogger(__name__)


class AgentFileUploadService:
    """Manages file uploads to per-agent S3 buckets.

    Each agent instance gets a dedicated bucket so users can only upload
    files to the agent they have access to — no cross-agent IDOR possible.
    """

    UPLOAD_URL_LIFETIME_SECONDS = 3600  # 1 hour

    def __init__(
        self,
        s3_client: S3Client,
        s3_public_client: S3Client,
        s3_settings: S3StorageSettings,
    ):
        self._s3_client = s3_client
        self._s3_public_client = s3_public_client
        self._s3_settings = s3_settings
        self._known_buckets: set[str] = set()

    @staticmethod
    def bucket_name(agent_class: str, agent_id: str) -> str:
        """Deterministic, S3-safe bucket name for an agent instance's file uploads.

        Convention: ``agent-files-{agent_class}-{agent_id}`` — lowercased, with
        only alphanumerics and hyphens. S3 bucket names must be 3-63 characters,
        lowercase, no underscores.
        """
        raw = f"agent-files-{agent_class}-{agent_id}"
        sanitized = re.sub(r"[^a-z0-9-]", "-", raw.lower())
        sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")

        if len(sanitized) < 3:
            sanitized = sanitized.ljust(3, "0")
        if len(sanitized) > 63:
            sanitized = sanitized[:63].rstrip("-")

        return sanitized

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """Idempotent bucket creation with in-memory caching."""
        if bucket_name in self._known_buckets:
            return

        try:
            self._s3_client.head_bucket(Bucket=bucket_name)
            self._known_buckets.add(bucket_name)
            return
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code not in ["404", "NoSuchBucket"]:
                raise

        logger.info(f"Creating agent upload bucket: {bucket_name}")
        self._s3_client.create_bucket(Bucket=bucket_name)
        self._known_buckets.add(bucket_name)

    @staticmethod
    def s3_key(file_id: str, filename: str) -> str:
        return f"{file_id}/{filename}"

    @trace_fn
    def generate_upload_url(self, agent_class: str, agent_id: str, content_type: str, filename: str) -> tuple[str, str]:
        """Generate a presigned PUT URL for uploading a file to the agent's bucket.

        Returns (presigned_url, file_id).
        """
        bucket = self.bucket_name(agent_class, agent_id)
        self._ensure_bucket_exists(bucket)

        file_id = str(uuid.uuid4())
        key = self.s3_key(file_id, filename)

        presigned_url = self._s3_public_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=self.UPLOAD_URL_LIFETIME_SECONDS,
        )

        logger.debug(f"Generated upload URL for {bucket}/{key}")
        return presigned_url, file_id

    @trace_fn
    def verify_file_exists(self, agent_class: str, agent_id: str, file_id: str, filename: str) -> bool:
        """Check whether a file was successfully uploaded to the agent's bucket."""
        bucket = self.bucket_name(agent_class, agent_id)
        key = self.s3_key(file_id, filename)
        try:
            self._s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ["404", "NoSuchKey"]:
                return False
            raise

    @trace_fn
    def delete_file(self, agent_class: str, agent_id: str, file_id: str, filename: str) -> None:
        """Delete a specific file from the agent's bucket."""
        bucket = self.bucket_name(agent_class, agent_id)
        key = self.s3_key(file_id, filename)
        self._s3_client.delete_object(Bucket=bucket, Key=key)
        logger.debug(f"Deleted {bucket}/{key}")
