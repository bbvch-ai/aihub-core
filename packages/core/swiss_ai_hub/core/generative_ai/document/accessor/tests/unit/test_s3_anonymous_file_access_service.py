from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)


def _create_service(s3_client: MagicMock | None = None) -> S3AnonymousFileAccessService:
    return S3AnonymousFileAccessService(
        s3_client=s3_client or MagicMock(),
        s3_public_client=MagicMock(),
        s3_settings=MagicMock(),
    )


def test_download_file_returns_raw_bytes():
    content = b"hello world"
    body_mock = MagicMock()
    body_mock.read.return_value = content

    s3_client = MagicMock()
    s3_client.get_object.return_value = {"Body": body_mock}

    service = _create_service(s3_client)
    result = service.download_file("my-bucket", "path/to/file.txt")

    assert result == content
    s3_client.get_object.assert_called_once_with(Bucket="my-bucket", Key="path/to/file.txt")
    body_mock.close.assert_called_once()


def test_download_file_closes_body_on_read_error():
    body_mock = MagicMock()
    body_mock.read.side_effect = OSError("read failed")

    s3_client = MagicMock()
    s3_client.get_object.return_value = {"Body": body_mock}

    service = _create_service(s3_client)

    with pytest.raises(IOError, match="read failed"):
        service.download_file("my-bucket", "path/to/file.txt")

    body_mock.close.assert_called_once()


@pytest.mark.parametrize(
    ("container", "file_path"),
    [
        ("", "path/to/file.txt"),
        ("  ", "path/to/file.txt"),
        ("my-bucket", ""),
        ("my-bucket", "  "),
    ],
)
def test_download_file_rejects_empty_params(container: str, file_path: str):
    service = _create_service()

    with pytest.raises(ValueError):
        service.download_file(container, file_path)


def test_delete_file_calls_delete_object():
    s3_client = MagicMock()
    service = _create_service(s3_client)

    service.delete_file("my-bucket", "namespace/file.pdf")

    s3_client.delete_object.assert_called_once_with(Bucket="my-bucket", Key="namespace/file.pdf")


@pytest.mark.parametrize(
    ("container", "file_path"),
    [
        ("", "path/to/file.txt"),
        ("  ", "path/to/file.txt"),
        ("my-bucket", ""),
        ("my-bucket", "  "),
    ],
)
def test_delete_file_rejects_empty_params(container: str, file_path: str):
    service = _create_service()

    with pytest.raises(ValueError):
        service.delete_file(container, file_path)
