import base64
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient

PLAIN_MD5_ETAG = "33d0c38d07a0671842cffe80c9973b8c"
CHUNKED_ETAG = "33d0c38d07a0671842cffe80c9973b8c-2"

NAMESPACE_PATCH_TARGET = (
    "swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client.get_or_create_namespace_for_directory"
)


def _make_s3_client(etag: str) -> MagicMock:
    mock = MagicMock()
    mock.head_object.return_value = {
        "ContentType": "application/pdf",
        "ETag": f'"{etag}"',
        "Metadata": {},
        "LastModified": datetime(2026, 7, 24, tzinfo=UTC),
        "ContentLength": 9_000_000,
    }
    return mock


def _make_s3_object(key: str, etag: str) -> dict:
    return {
        "Key": key,
        "Size": 9_000_000,
        "LastModified": datetime(2026, 7, 24, tzinfo=UTC),
        "ETag": f'"{etag}"',
    }


class TestCreateDataLakeFileFromS3Object:
    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_chunked_etag_is_kept_verbatim(self, _namespace: MagicMock) -> None:
        client = S3DataLakeClient(container_name="bucket", s3_client=_make_s3_client(CHUNKED_ETAG))

        data_lake_file = client._create_data_lake_file_from_s3_object(
            "s3://bucket/docs/large.pdf", _make_s3_object("docs/large.pdf", CHUNKED_ETAG), "docs/large.pdf"
        )

        assert data_lake_file.hash == CHUNKED_ETAG

    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_plain_md5_etag_stays_base64_encoded(self, _namespace: MagicMock) -> None:
        client = S3DataLakeClient(container_name="bucket", s3_client=_make_s3_client(PLAIN_MD5_ETAG))

        data_lake_file = client._create_data_lake_file_from_s3_object(
            "s3://bucket/docs/small.pdf", _make_s3_object("docs/small.pdf", PLAIN_MD5_ETAG), "docs/small.pdf"
        )

        assert data_lake_file.hash == base64.b64encode(bytes.fromhex(PLAIN_MD5_ETAG)).decode("utf-8")


class TestGetAllFiles:
    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_mixed_etag_formats_all_enumerate(self, _namespace: MagicMock) -> None:
        s3_client = _make_s3_client(PLAIN_MD5_ETAG)
        s3_client.get_paginator.return_value.paginate.return_value = [
            {
                "Contents": [
                    _make_s3_object("docs/small.pdf", PLAIN_MD5_ETAG),
                    _make_s3_object("docs/large.pdf", CHUNKED_ETAG),
                ]
            }
        ]
        s3_client.head_object.side_effect = lambda Bucket, Key: {  # noqa: N803
            "ContentType": "application/pdf",
            "ETag": f'"{CHUNKED_ETAG if "large" in Key else PLAIN_MD5_ETAG}"',
            "Metadata": {},
            "LastModified": datetime(2026, 7, 24, tzinfo=UTC),
        }

        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)

        files = client.get_all_files()

        assert [file.hash for file in files] == [
            base64.b64encode(bytes.fromhex(PLAIN_MD5_ETAG)).decode("utf-8"),
            CHUNKED_ETAG,
        ]
