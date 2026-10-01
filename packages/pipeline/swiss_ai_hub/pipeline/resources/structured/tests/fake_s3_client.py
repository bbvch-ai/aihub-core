"""The slice of boto3's S3 client the structured destination and state store use, kept in a dict."""

import io
from typing import Any

from botocore.exceptions import ClientError


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict[str, Any]] = {}
        self.put_attempts = 0
        self.fail_next_puts_with: list[str] = []

    def put_object(self, *, Bucket: str, Key: str, Body: bytes | str, Metadata: dict | None = None, **params: Any):
        self.put_attempts += 1
        if self.fail_next_puts_with:
            raise ClientError({"Error": {"Code": self.fail_next_puts_with.pop(0), "Message": "fake"}}, "PutObject")
        body = Body.encode() if isinstance(Body, str) else Body
        self.objects[(Bucket, Key)] = {"Body": body, "Metadata": dict(Metadata or {}), **params}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        return {"Metadata": self._stored(Bucket, Key, "HeadObject", "404")["Metadata"]}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        return {"Body": io.BytesIO(self._stored(Bucket, Key, "GetObject", "NoSuchKey")["Body"])}

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.objects.pop((Bucket, Key), None)

    def keys(self, bucket: str) -> list[str]:
        return sorted(key for stored_bucket, key in self.objects if stored_bucket == bucket)

    def _stored(self, bucket: str, key: str, operation: str, missing_code: str) -> dict[str, Any]:
        if (bucket, key) not in self.objects:
            raise ClientError({"Error": {"Code": missing_code, "Message": "missing"}}, operation)
        return self.objects[(bucket, key)]
