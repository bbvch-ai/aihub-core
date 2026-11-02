"""The slice of boto3's S3 client the structured destination and state store use, kept in a dict."""

import hashlib
import io
from collections.abc import Iterator
from typing import Any

from botocore.exceptions import ClientError


class FakeS3Client:
    """Callers pass boto3's capitalised keywords (``Bucket=``, ``Key=``), so the methods read them from ``params``
    instead of declaring parameters under names Python style would not use."""

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict[str, Any]] = {}
        self.put_attempts = 0
        self.put_keys: list[tuple[str, str]] = []
        self.fail_next_puts_with: list[str] = []
        self.succeed_puts_before_failing = 0

    def put_object(self, **params: Any) -> None:
        bucket, key, body = params.pop("Bucket"), params.pop("Key"), params.pop("Body")
        metadata = params.pop("Metadata", None)
        self.put_attempts += 1
        self.put_keys.append((bucket, key))
        if self.fail_next_puts_with and self.put_attempts > self.succeed_puts_before_failing:
            raise ClientError({"Error": {"Code": self.fail_next_puts_with.pop(0), "Message": "fake"}}, "PutObject")
        content = body.encode() if isinstance(body, str) else body
        self.objects[(bucket, key)] = {"Body": content, "Metadata": dict(metadata or {}), **params}

    def head_object(self, **params: Any) -> dict[str, Any]:
        """The ETag as S3 and SeaweedFS report it for a single-part upload: the quoted hex MD5 of the body."""
        stored = self._stored(params["Bucket"], params["Key"], "HeadObject", "404")
        etag = hashlib.md5(stored["Body"], usedforsecurity=False).hexdigest()
        return {"Metadata": stored["Metadata"], "ETag": f'"{etag}"'}

    def get_object(self, **params: Any) -> dict[str, Any]:
        return {"Body": io.BytesIO(self._stored(params["Bucket"], params["Key"], "GetObject", "NoSuchKey")["Body"])}

    def delete_object(self, **params: Any) -> None:
        self.objects.pop((params["Bucket"], params["Key"]), None)

    def keys(self, bucket: str) -> list[str]:
        return sorted(key for stored_bucket, key in self.objects if stored_bucket == bucket)

    def list_objects_v2(self, **params: Any) -> dict[str, Any]:
        prefix = params.get("Prefix", "")
        matching = [{"Key": key} for key in self.keys(params["Bucket"]) if key.startswith(prefix)]
        return {"Contents": matching} if matching else {}

    def get_paginator(self, operation: str) -> "FakeS3Client._ListObjectsPaginator":
        if operation != "list_objects_v2":
            raise NotImplementedError(operation)
        return self._ListObjectsPaginator(self)

    class _ListObjectsPaginator:
        def __init__(self, client: "FakeS3Client") -> None:
            self.client = client

        def paginate(self, **params: Any) -> Iterator[dict[str, Any]]:
            yield {"Contents": [{"Key": key} for key in self.client.keys(params["Bucket"])]}

    def _stored(self, bucket: str, key: str, operation: str, missing_code: str) -> dict[str, Any]:
        if (bucket, key) not in self.objects:
            raise ClientError({"Error": {"Code": missing_code, "Message": "missing"}}, operation)
        return self.objects[(bucket, key)]
