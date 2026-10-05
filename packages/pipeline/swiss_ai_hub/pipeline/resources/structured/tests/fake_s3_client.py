"""The slice of boto3's S3 client the structured destination and state store use, kept in a dict."""

import hashlib
import io
from typing import Any

from botocore.exceptions import ClientError


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict[str, Any]] = {}
        self.put_attempts = 0
        self.put_keys: list[tuple[str, str]] = []
        self.fail_next_puts_with: list[str] = []
        self.succeed_puts_before_failing = 0

    def put_object(self, *, Bucket: str, Key: str, Body: bytes | str, Metadata: dict | None = None, **params: Any):
        self.put_attempts += 1
        self.put_keys.append((Bucket, Key))
        if self.fail_next_puts_with and self.put_attempts > self.succeed_puts_before_failing:
            raise ClientError({"Error": {"Code": self.fail_next_puts_with.pop(0), "Message": "fake"}}, "PutObject")
        body = Body.encode() if isinstance(Body, str) else Body
        self.objects[(Bucket, Key)] = {"Body": body, "Metadata": dict(Metadata or {}), **params}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        """The ETag as S3 and SeaweedFS report it for a single-part upload: the quoted hex MD5 of the body."""
        stored = self._stored(Bucket, Key, "HeadObject", "404")
        return {"Metadata": stored["Metadata"], "ETag": f'"{hashlib.md5(stored["Body"]).hexdigest()}"'}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, Any]:
        return {"Body": io.BytesIO(self._stored(Bucket, Key, "GetObject", "NoSuchKey")["Body"])}

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.objects.pop((Bucket, Key), None)

    def keys(self, bucket: str) -> list[str]:
        return sorted(key for stored_bucket, key in self.objects if stored_bucket == bucket)

    def list_objects_v2(self, *, Bucket: str, Prefix: str = "", **_: Any) -> dict[str, Any]:
        matching = [{"Key": key} for key in self.keys(Bucket) if key.startswith(Prefix)]
        return {"Contents": matching} if matching else {}

    def get_paginator(self, operation: str) -> "FakeS3Client._ListObjectsPaginator":
        if operation != "list_objects_v2":
            raise NotImplementedError(operation)
        return self._ListObjectsPaginator(self)

    class _ListObjectsPaginator:
        def __init__(self, client: "FakeS3Client") -> None:
            self.client = client

        def paginate(self, *, Bucket: str, **_: Any):
            yield {"Contents": [{"Key": key} for key in self.client.keys(Bucket)]}

    def _stored(self, bucket: str, key: str, operation: str, missing_code: str) -> dict[str, Any]:
        if (bucket, key) not in self.objects:
            raise ClientError({"Error": {"Code": missing_code, "Message": "missing"}}, operation)
        return self.objects[(bucket, key)]
