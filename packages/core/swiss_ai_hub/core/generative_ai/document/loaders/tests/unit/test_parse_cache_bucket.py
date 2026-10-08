from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from swiss_ai_hub.core.generative_ai.document.loaders.parse_cache_bucket import ParseCacheBucket


def bucket_with(client: MagicMock, monkeypatch: pytest.MonkeyPatch) -> ParseCacheBucket:
    bucket = ParseCacheBucket()
    monkeypatch.setattr(bucket, "_client", lambda: client)
    return bucket


def test_the_s3_body_is_closed_after_a_hit(monkeypatch: pytest.MonkeyPatch):
    body = MagicMock()
    body.read.return_value = b"cached"
    client = MagicMock()
    client.get_object.return_value = {"Body": body}

    assert bucket_with(client, monkeypatch).read("mineru/key") == b"cached"
    client.get_object.assert_called_once_with(Bucket="parse-cache", Key="mineru/key")
    body.close.assert_called_once()


@pytest.mark.parametrize("code", ["NoSuchKey", "404"])
def test_a_missing_entry_is_a_miss(code: str, monkeypatch: pytest.MonkeyPatch):
    client = MagicMock()
    client.get_object.side_effect = ClientError({"Error": {"Code": code}}, "GetObject")

    assert bucket_with(client, monkeypatch).read("markitdown/key") is None


def test_any_other_storage_error_propagates(monkeypatch: pytest.MonkeyPatch):
    client = MagicMock()
    client.get_object.side_effect = ClientError({"Error": {"Code": "NoSuchBucket"}}, "GetObject")

    with pytest.raises(ClientError):
        bucket_with(client, monkeypatch).read("markitdown/key")


def test_write_stores_the_content_with_its_type(monkeypatch: pytest.MonkeyPatch):
    client = MagicMock()

    bucket_with(client, monkeypatch).write("markitdown/key", b"# text", "text/markdown; charset=utf-8")

    client.put_object.assert_called_once_with(
        Bucket="parse-cache", Key="markitdown/key", Body=b"# text", ContentType="text/markdown; charset=utf-8"
    )
