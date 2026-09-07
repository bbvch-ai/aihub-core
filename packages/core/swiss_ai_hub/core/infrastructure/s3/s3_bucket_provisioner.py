import logging
from typing import Annotated, Any, ClassVar

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)

_MISSING_BUCKET_ERROR_CODES = ("404", "NoSuchBucket")


class S3BucketProvisioner:
    """Creates data-lake buckets with the CORS ruleset browser uploads need.

    Both the API (at create-database time) and the pipeline (on its first ingest) may be the first to
    touch a bucket, and ``put_bucket_cors`` replaces the whole configuration rather than merging it, so
    each rewrites whatever the other wrote. They therefore share one ruleset here; keeping a second copy
    is how the two silently drifted before.
    """

    # AllowedOrigins is "*" by design: the entitlement lives in the short-lived, signed presigned URL,
    # not in CORS. The origin we would otherwise pin is the browser app's own domain (Admin UI /
    # OpenWebUI), which is deployment-specific and not known to these S3 settings — PUBLIC_ENDPOINT is
    # the S3 host, not the frontend host. Narrow this to the frontend origin only once it is configurable.
    # Keep in sync with infra/configs/seaweedfs/init-buckets.sh, which provisions the built-in buckets.
    CORS_RULES: ClassVar[list[dict[str, Any]]] = [
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

    @staticmethod
    def bucket_exists(
        client: Annotated[S3Client, "Client with write access to the storage backend"],
        bucket: Annotated[str, "Bucket to look up"],
    ) -> bool:
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError as error:
            if error.response["Error"]["Code"] in _MISSING_BUCKET_ERROR_CODES:
                return False
            raise
        return True

    @classmethod
    def ensure_bucket_with_cors(
        cls,
        client: Annotated[S3Client, "Client with write access to the storage backend"],
        bucket: Annotated[str, "Bucket to create if missing and configure"],
    ) -> None:
        """Idempotently creates the bucket and writes the shared CORS ruleset."""
        if not cls.bucket_exists(client, bucket):
            client.create_bucket(Bucket=bucket)
            logger.info(f"Created S3 bucket '{bucket}'")

        client.put_bucket_cors(Bucket=bucket, CORSConfiguration={"CORSRules": cls.CORS_RULES})
