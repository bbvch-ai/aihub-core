import logging
import re
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from aihub_backup.models import TIMESTAMP_LENGTH
from aihub_backup.settings import BackupSettings

logger = logging.getLogger(__name__)

BACKUP_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_(online|offline)$")

_S3_DELETE_BATCH_SIZE = 1000


class S3Manager:
    def __init__(self, settings: BackupSettings) -> None:
        self._bucket = settings.BACKUP_S3_BUCKET
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.AWS_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY.get_secret_value(),
            config=Config(signature_version="s3v4"),
        )

    @property
    def bucket(self) -> str:
        return self._bucket

    def ensure_bucket_exists(self) -> None:
        """SeaweedFS auto-creates paths on write but skips bucket metadata,
        which breaks HeadObject. Explicit creation avoids this.
        """
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code not in ("404", "NoSuchBucket"):
                raise
            logger.info("Creating S3 bucket: %s", self._bucket)
            try:
                self._client.create_bucket(Bucket=self._bucket)
            except ClientError as create_err:
                code = create_err.response.get("Error", {}).get("Code", "")
                if code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists", "409"):
                    raise

    def upload_file(self, local_path: Path, s3_key: str) -> None:
        logger.info("Uploading %s -> s3://%s/%s", local_path, self._bucket, s3_key)
        self._client.upload_file(str(local_path), self._bucket, s3_key)

    def download_file(self, s3_key: str, local_path: Path) -> None:
        logger.info("Downloading s3://%s/%s -> %s", self._bucket, s3_key, local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(self._bucket, s3_key, str(local_path))

    def file_exists(self, s3_key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code", "") in ("404", "NoSuchKey"):
                return False
            raise

    def list_prefixes(self, prefix: str = "") -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        prefixes: list[str] = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                prefixes.append(cp["Prefix"].rstrip("/"))
        return prefixes

    def count_objects(self, prefix: str) -> int:
        paginator = self._client.get_paginator("list_objects_v2")
        count = 0
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            count += page.get("KeyCount", 0)
        return count

    def delete_recursive(self, prefix: str) -> None:
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            objects: list[dict[str, str]] = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            for i in range(0, len(objects), _S3_DELETE_BATCH_SIZE):
                batch = objects[i : i + _S3_DELETE_BATCH_SIZE]
                self._client.delete_objects(Bucket=self._bucket, Delete={"Objects": batch})
        logger.info("Deleted s3://%s/%s", self._bucket, prefix)

    def resolve_timestamp(self, timestamp: str) -> str:
        """When both _online and _offline exist for a timestamp, prefers offline."""
        prefixes = self.list_prefixes()

        if timestamp in prefixes:
            return timestamp

        # Offline last so it wins when both exist
        found = ""
        for suffix in ("online", "offline"):
            candidate = f"{timestamp}_{suffix}"
            if candidate in prefixes:
                found = candidate

        if found:
            return found
        raise ValueError(f"No backup found matching timestamp: {timestamp}")

    def find_latest_backup(self) -> str | None:
        """Prefers offline over online when both exist for the same timestamp."""
        prefixes = self.list_prefixes()
        backup_prefixes = [p for p in prefixes if BACKUP_PREFIX_RE.match(p)]
        if not backup_prefixes:
            return None
        # Sort by (timestamp, mode_rank) so offline (rank 1) beats online (rank 0)
        return sorted(backup_prefixes, key=lambda p: (p[:TIMESTAMP_LENGTH], p.endswith("_offline")))[-1]
