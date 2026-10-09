from typing import TYPE_CHECKING, ClassVar

from botocore.exceptions import ClientError

from swiss_ai_hub.core.infrastructure.s3.use_s3 import create_s3_client

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class ParseCacheBucket:
    """
    The bucket the document loaders keep their conversions in, so each loader's cache only decides its keys.

    Entries expire through the bucket's lifecycle rule (`s3-init-buckets.sh.j2`); an expired entry is simply
    converted again.
    """

    NAME: ClassVar[str] = "parse-cache"

    def __init__(self) -> None:
        self._s3_client: S3Client | None = None

    def read(self, key: str) -> bytes | None:
        try:
            response = self._client().get_object(Bucket=self.NAME, Key=key)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                return None
            raise
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def write(self, key: str, content: bytes, content_type: str) -> None:
        self._client().put_object(Bucket=self.NAME, Key=key, Body=content, ContentType=content_type)

    def _client(self) -> "S3Client":
        """Built on first use in a worker thread: creating a boto3 client blocks for tens of milliseconds."""
        if self._s3_client is None:
            self._s3_client = create_s3_client()
        return self._s3_client
