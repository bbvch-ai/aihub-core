from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)


def _create_service(s3_client: MagicMock | None = None) -> S3AnonymousFileAccessService:
    return S3AnonymousFileAccessService(
        s3_client=s3_client or MagicMock(),
        s3_public_client=MagicMock(),
        s3_settings=MagicMock(),
    )


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code}}, "DeleteBucket")


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


def test_generate_sas_url_uses_public_client_by_default():
    s3_client = MagicMock()
    s3_public_client = MagicMock()
    s3_public_client.generate_presigned_url.return_value = "https://public/signed"
    service = S3AnonymousFileAccessService(
        s3_client=s3_client,
        s3_public_client=s3_public_client,
        s3_settings=MagicMock(),
    )

    result = service.generate_sas_url("my-bucket", "path/to/figure.png")

    assert result == "https://public/signed"
    s3_public_client.generate_presigned_url.assert_called_once()
    s3_client.generate_presigned_url.assert_not_called()


def test_generate_sas_url_uses_internal_client_when_internal():
    s3_client = MagicMock()
    s3_internal_client = MagicMock()
    s3_internal_client.generate_presigned_url.return_value = "http://internal/signed"
    s3_public_client = MagicMock()
    service = S3AnonymousFileAccessService(
        s3_client=s3_client,
        s3_public_client=s3_public_client,
        s3_settings=MagicMock(),
        s3_internal_client=s3_internal_client,
    )

    result = service.generate_sas_url("my-bucket", "path/to/figure.png", internal=True)

    assert result == "http://internal/signed"
    s3_internal_client.generate_presigned_url.assert_called_once()
    s3_public_client.generate_presigned_url.assert_not_called()
    s3_client.generate_presigned_url.assert_not_called()


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


def test_delete_container_empties_bucket_before_deleting_it():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "ns/a.pdf"}, {"Key": "ns/b.pdf"}]},
        {},
    ]
    service = _create_service(s3_client)

    service.delete_container("my-bucket")

    s3_client.delete_objects.assert_called_once_with(
        Bucket="my-bucket", Delete={"Objects": [{"Key": "ns/a.pdf"}, {"Key": "ns/b.pdf"}]}
    )
    s3_client.delete_bucket.assert_called_once_with(Bucket="my-bucket")


def test_delete_container_skips_delete_objects_when_already_empty():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [{}]
    service = _create_service(s3_client)

    service.delete_container("my-bucket")

    s3_client.delete_objects.assert_not_called()
    s3_client.delete_bucket.assert_called_once_with(Bucket="my-bucket")


def test_delete_container_is_idempotent_when_bucket_is_missing():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [{}]
    s3_client.delete_bucket.side_effect = _client_error("NoSuchBucket")
    service = _create_service(s3_client)

    service.delete_container("my-bucket")


def test_delete_container_reraises_unexpected_errors():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [{}]
    s3_client.delete_bucket.side_effect = _client_error("AccessDenied")
    service = _create_service(s3_client)

    with pytest.raises(ClientError):
        service.delete_container("my-bucket")


@pytest.mark.parametrize("container", ["", "  "])
def test_delete_container_rejects_empty_name(container: str):
    service = _create_service()

    with pytest.raises(ValueError):
        service.delete_container(container)


def test_delete_prefix_deletes_objects_under_prefix_without_deleting_the_bucket():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "folder/a.pdf"}, {"Key": "folder/b.pdf"}]},
        {},
    ]
    service = _create_service(s3_client)

    service.delete_prefix("my-bucket", "folder/")

    s3_client.get_paginator.return_value.paginate.assert_called_once_with(Bucket="my-bucket", Prefix="folder/")
    s3_client.delete_objects.assert_called_once_with(
        Bucket="my-bucket", Delete={"Objects": [{"Key": "folder/a.pdf"}, {"Key": "folder/b.pdf"}]}
    )
    s3_client.delete_bucket.assert_not_called()


def test_delete_prefix_skips_delete_objects_when_prefix_is_empty():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.return_value = [{}]
    service = _create_service(s3_client)

    service.delete_prefix("my-bucket", "folder/")

    s3_client.delete_objects.assert_not_called()


def test_delete_prefix_is_idempotent_when_bucket_is_missing():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.side_effect = _client_error("NoSuchBucket")
    service = _create_service(s3_client)

    service.delete_prefix("my-bucket", "folder/")


def test_delete_prefix_reraises_unexpected_errors():
    s3_client = MagicMock()
    s3_client.get_paginator.return_value.paginate.side_effect = _client_error("AccessDenied")
    service = _create_service(s3_client)

    with pytest.raises(ClientError):
        service.delete_prefix("my-bucket", "folder/")


@pytest.mark.parametrize(
    ("container", "prefix"), [("", "folder/"), ("  ", "folder/"), ("my-bucket", ""), ("my-bucket", "  ")]
)
def test_delete_prefix_rejects_empty_params(container: str, prefix: str):
    service = _create_service()

    with pytest.raises(ValueError):
        service.delete_prefix(container, prefix)
