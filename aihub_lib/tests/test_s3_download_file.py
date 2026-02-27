from unittest.mock import MagicMock

from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService


def test_download_file_returns_raw_bytes():
    content = b"hello world"
    body_mock = MagicMock()
    body_mock.read.return_value = content

    s3_client = MagicMock()
    s3_client.get_object.return_value = {"Body": body_mock}

    service = S3AnonymousFileAccessService(
        s3_client=s3_client,
        s3_public_client=MagicMock(),
        s3_settings=MagicMock(),
    )

    result = service.download_file("my-bucket", "path/to/file.txt")

    assert result == content
    s3_client.get_object.assert_called_once_with(Bucket="my-bucket", Key="path/to/file.txt")
