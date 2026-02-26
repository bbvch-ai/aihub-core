import logging
import uuid

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings

logger = logging.getLogger(__name__)


class AgentFileUploadService:
    """Manages file uploads to a single shared S3 bucket with path-based isolation.

    All agent files live in one bucket (``agent-files``). Each file is stored
    under ``{agent_class}/{agent_id}/{file_id}/{filename}`` — access control
    is enforced at the API layer via permissions.
    """

    BUCKET_NAME = "agent-files"
    UPLOAD_URL_LIFETIME_SECONDS = 3600  # 1 hour
    FILE_EXPIRATION_DAYS = 7

    def __init__(
        self,
        s3_client: S3Client,
        s3_public_client: S3Client,
        s3_settings: S3StorageSettings,
    ):
        self._s3_client = s3_client
        self._s3_public_client = s3_public_client
        self._s3_settings = s3_settings

    def ensure_bucket_exists(self) -> None:
        """Idempotent creation of the shared agent-files bucket. Call once at API startup."""
        try:
            self._s3_client.head_bucket(Bucket=self.BUCKET_NAME)
            return
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code not in ["404", "NoSuchBucket"]:
                raise

        logger.info(f"Creating agent upload bucket: {self.BUCKET_NAME}")
        self._s3_client.create_bucket(Bucket=self.BUCKET_NAME)
        self._s3_client.put_bucket_lifecycle_configuration(
            Bucket=self.BUCKET_NAME,
            LifecycleConfiguration={
                "Rules": [
                    {
                        "ID": "auto-expire-agent-files",
                        "Status": "Enabled",
                        "Expiration": {"Days": self.FILE_EXPIRATION_DAYS},
                    }
                ]
            },
        )

    @staticmethod
    def _sanitize_path_segment(value: str) -> str:
        """Remove path separators and traversal characters from a single path segment."""
        return value.replace("/", "_").replace("\\", "_").replace("..", "_")

    @staticmethod
    def s3_key(agent_class: str, agent_id: str, file_id: str, filename: str) -> str:
        safe_class = AgentFileUploadService._sanitize_path_segment(agent_class)
        safe_id = AgentFileUploadService._sanitize_path_segment(agent_id)
        safe_name = AgentFileUploadService._sanitize_path_segment(filename)
        return f"{safe_class}/{safe_id}/{file_id}/{safe_name}"

    @trace_fn
    def generate_upload_url(self, agent_class: str, agent_id: str, content_type: str, filename: str) -> tuple[str, str]:
        """Generate a presigned PUT URL for uploading a file.

        Returns (presigned_url, file_id).
        """
        file_id = str(uuid.uuid4())
        key = self.s3_key(agent_class, agent_id, file_id, filename)

        presigned_url = self._s3_public_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.BUCKET_NAME, "Key": key, "ContentType": content_type},
            ExpiresIn=self.UPLOAD_URL_LIFETIME_SECONDS,
        )

        logger.debug(f"Generated upload URL for {self.BUCKET_NAME}/{key}")
        return presigned_url, file_id

    @trace_fn
    def verify_file_exists(self, agent_class: str, agent_id: str, file_id: str, filename: str) -> bool:
        """Check whether a file was successfully uploaded."""
        key = self.s3_key(agent_class, agent_id, file_id, filename)
        try:
            self._s3_client.head_object(Bucket=self.BUCKET_NAME, Key=key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ["404", "NoSuchKey"]:
                return False
            raise

    @trace_fn
    def delete_file(self, agent_class: str, agent_id: str, file_id: str, filename: str) -> None:
        """Delete a specific file."""
        key = self.s3_key(agent_class, agent_id, file_id, filename)
        self._s3_client.delete_object(Bucket=self.BUCKET_NAME, Key=key)
        logger.debug(f"Deleted {self.BUCKET_NAME}/{key}")
