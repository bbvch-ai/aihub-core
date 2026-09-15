import base64
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient

PLAIN_MD5_ETAG = "33d0c38d07a0671842cffe80c9973b8c"
CHUNKED_ETAG = "33d0c38d07a0671842cffe80c9973b8c-2"

NAMESPACE_PATCH_TARGET = (
    "swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client.get_or_create_namespace_for_directory"
)

LAST_MODIFIED = datetime(2026, 7, 24, tzinfo=UTC)


def _make_s3_client(etag: str) -> MagicMock:
    mock = MagicMock()
    mock.head_object.return_value = {
        "ContentType": "application/pdf",
        "ETag": f'"{etag}"',
        "Metadata": {},
        "LastModified": LAST_MODIFIED,
        "ContentLength": 9_000_000,
    }
    return mock


def _make_s3_object(key: str, etag: str) -> dict:
    return {
        "Key": key,
        "Size": 9_000_000,
        "LastModified": LAST_MODIFIED,
        "ETag": f'"{etag}"',
    }


def _paginating(s3_client: MagicMock, keys_with_etags: list[tuple[str, str]]) -> MagicMock:
    s3_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [_make_s3_object(key, etag) for key, etag in keys_with_etags]}
    ]
    return s3_client


class TestCreateDataLakeFileFromS3Object:
    def test_chunked_etag_is_kept_verbatim(self) -> None:
        client = S3DataLakeClient(container_name="bucket", s3_client=_make_s3_client(CHUNKED_ETAG))

        data_lake_file = client._create_data_lake_file_from_s3_object(
            "s3://bucket/docs/large.pdf",
            _make_s3_object("docs/large.pdf", CHUNKED_ETAG),
            "docs/large.pdf",
            namespace="docs",
        )

        assert data_lake_file.hash == CHUNKED_ETAG

    def test_plain_md5_etag_stays_base64_encoded(self) -> None:
        client = S3DataLakeClient(container_name="bucket", s3_client=_make_s3_client(PLAIN_MD5_ETAG))

        data_lake_file = client._create_data_lake_file_from_s3_object(
            "s3://bucket/docs/small.pdf",
            _make_s3_object("docs/small.pdf", PLAIN_MD5_ETAG),
            "docs/small.pdf",
            namespace="docs",
        )

        assert data_lake_file.hash == base64.b64encode(bytes.fromhex(PLAIN_MD5_ETAG)).decode("utf-8")


class TestDataVersionParity:
    """The DataVersion is ``f"{updated}-{hash}"``. If either half differed between the listing and
    the head, the first observation after deploy would mark every partition changed and re-parse
    and re-embed the entire corpus."""

    def _both_paths(self, etag: str) -> tuple[tuple[str, int], tuple[str, int]]:
        s3_client = _make_s3_client(etag)
        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)
        s3_object = _make_s3_object("docs/file.pdf", etag)
        head_response = s3_client.head_object(Bucket="bucket", Key="docs/file.pdf")

        from_head = client._create_data_lake_file_from_s3_object(
            "s3://bucket/docs/file.pdf", s3_object, "docs/file.pdf", namespace="docs", head_response=head_response
        )
        from_listing = client._create_data_lake_file_from_s3_object(
            "s3://bucket/docs/file.pdf", s3_object, "docs/file.pdf", namespace="docs"
        )
        return (from_head.hash, from_head.updated), (from_listing.hash, from_listing.updated)

    def test_plain_md5_branch_is_identical_on_both_paths(self) -> None:
        from_head, from_listing = self._both_paths(PLAIN_MD5_ETAG)

        assert from_head == from_listing

    def test_chunked_branch_is_identical_on_both_paths(self) -> None:
        from_head, from_listing = self._both_paths(CHUNKED_ETAG)

        assert from_head == from_listing


class TestGetAllFiles:
    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_mixed_etag_formats_all_enumerate(self, _namespace: MagicMock) -> None:
        s3_client = _paginating(
            _make_s3_client(PLAIN_MD5_ETAG),
            [("docs/small.pdf", PLAIN_MD5_ETAG), ("docs/large.pdf", CHUNKED_ETAG)],
        )

        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)

        files = client.get_all_files()

        assert [file.hash for file in files] == [
            base64.b64encode(bytes.fromhex(PLAIN_MD5_ETAG)).decode("utf-8"),
            CHUNKED_ETAG,
        ]

    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_does_not_head_each_object(self, _namespace: MagicMock) -> None:
        """``list_objects_v2`` already carries size, ETag and modification time, and the
        observation reads nothing else."""
        s3_client = _paginating(
            _make_s3_client(PLAIN_MD5_ETAG),
            [(f"docs/file{index}.pdf", PLAIN_MD5_ETAG) for index in range(25)],
        )
        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)
        s3_client.head_object.reset_mock()

        client.get_all_files()

        s3_client.head_object.assert_not_called()

    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_namespace_is_resolved_once_per_directory(self, namespace: MagicMock) -> None:
        s3_client = _paginating(
            _make_s3_client(PLAIN_MD5_ETAG),
            [(f"docs/file{index}.pdf", PLAIN_MD5_ETAG) for index in range(25)],
        )
        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)

        client.get_all_files()

        assert namespace.call_count == 1

    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_each_directory_is_still_registered(self, namespace: MagicMock) -> None:
        """The lookup also creates the NamespaceEntity the knowledge UI and namespace-selection
        agent read, so every directory must reach it at least once."""
        s3_client = _paginating(
            _make_s3_client(PLAIN_MD5_ETAG),
            [("docs/a.pdf", PLAIN_MD5_ETAG), ("reports/b.pdf", PLAIN_MD5_ETAG), ("docs/c.pdf", PLAIN_MD5_ETAG)],
        )
        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)

        client.get_all_files()

        assert namespace.call_count == 2
        assert {call.args[1] for call in namespace.call_args_list} == {"docs", "reports"}


class TestCreateDataLakeFileFromUri:
    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_heads_the_object_exactly_once(self, _namespace: MagicMock) -> None:
        """The download path needs the object's user metadata, but one head is enough for it."""
        s3_client = _make_s3_client(PLAIN_MD5_ETAG)
        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)
        s3_client.head_object.reset_mock()

        client.create_data_lake_file_from_uri("s3://bucket/docs/small.pdf")

        s3_client.head_object.assert_called_once()

    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_keeps_object_metadata(self, _namespace: MagicMock) -> None:
        s3_client = _make_s3_client(PLAIN_MD5_ETAG)
        s3_client.head_object.return_value = {
            **s3_client.head_object.return_value,
            "Metadata": {"namespace": "docs"},
        }
        client = S3DataLakeClient(container_name="bucket", s3_client=s3_client)

        data_lake_file = client.create_data_lake_file_from_uri("s3://bucket/docs/small.pdf")

        assert data_lake_file.metadata == {"namespace": "docs"}


class TestCreateDataLakeFilesFromUris:
    @patch(NAMESPACE_PATCH_TARGET, return_value="docs")
    def test_namespace_is_resolved_once_per_directory(self, namespace: MagicMock) -> None:
        """The removal job loads the whole corpus at once, where a per-file namespace lookup costs
        as much as it did in the observation."""
        client = S3DataLakeClient(container_name="bucket", s3_client=_make_s3_client(PLAIN_MD5_ETAG))

        files = client.create_data_lake_files_from_uris([f"s3://bucket/docs/file{index}.pdf" for index in range(25)])

        assert len(files) == 25
        assert namespace.call_count == 1
