from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from aihub_backup.s3 import S3Manager
from aihub_backup.settings import BackupSettings


@pytest.fixture
def s3_manager(settings: BackupSettings) -> S3Manager:
    with patch("aihub_backup.s3.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        manager = S3Manager(settings)
        manager._client = mock_client
        return manager


def test_resolve_timestamp_exact_match(s3_manager: S3Manager) -> None:
    """When the timestamp matches a directory exactly, return it unchanged."""
    s3_manager._client.get_paginator.return_value.paginate.return_value = [
        {"CommonPrefixes": [{"Prefix": "2026-02-18_14-00-00_online/"}]}
    ]
    result = s3_manager.resolve_timestamp("2026-02-18_14-00-00_online")
    assert result == "2026-02-18_14-00-00_online"


def test_resolve_timestamp_bare_prefers_offline(s3_manager: S3Manager) -> None:
    """When both online and offline exist, prefer offline."""
    s3_manager._client.get_paginator.return_value.paginate.return_value = [
        {
            "CommonPrefixes": [
                {"Prefix": "2026-02-18_14-00-00_online/"},
                {"Prefix": "2026-02-18_14-00-00_offline/"},
            ]
        }
    ]
    result = s3_manager.resolve_timestamp("2026-02-18_14-00-00")
    assert result == "2026-02-18_14-00-00_offline"


def test_resolve_timestamp_no_match_raises_value_error(s3_manager: S3Manager) -> None:
    """When no match is found, raise ValueError."""
    s3_manager._client.get_paginator.return_value.paginate.return_value = [{"CommonPrefixes": []}]
    with pytest.raises(ValueError, match="No backup found matching timestamp"):
        s3_manager.resolve_timestamp("2099-01-01_00-00-00")


def test_find_latest_backup(s3_manager: S3Manager) -> None:
    s3_manager._client.get_paginator.return_value.paginate.return_value = [
        {
            "CommonPrefixes": [
                {"Prefix": "2026-02-17_02-00-00_online/"},
                {"Prefix": "2026-02-18_02-00-00_online/"},
            ]
        }
    ]
    result = s3_manager.find_latest_backup()
    assert result == "2026-02-18_02-00-00_online"


def test_find_latest_backup_empty(s3_manager: S3Manager) -> None:
    s3_manager._client.get_paginator.return_value.paginate.return_value = [{"CommonPrefixes": []}]
    result = s3_manager.find_latest_backup()
    assert result is None


# ---------------------------------------------------------------------------
# Regression tests
# ---------------------------------------------------------------------------


def test_find_latest_backup_prefers_offline_over_online(s3_manager: S3Manager) -> None:
    """When both online and offline exist for the same timestamp, prefer offline.

    This must be consistent with resolve_timestamp which also prefers offline.
    Regression: find_latest_backup used plain lexicographic sort, which picked
    _online (o > f) instead of _offline for the same timestamp.
    """
    s3_manager._client.get_paginator.return_value.paginate.return_value = [
        {
            "CommonPrefixes": [
                {"Prefix": "2026-02-18_02-00-00_online/"},
                {"Prefix": "2026-02-18_02-00-00_offline/"},
            ]
        }
    ]
    result = s3_manager.find_latest_backup()
    assert result == "2026-02-18_02-00-00_offline"


# ---------------------------------------------------------------------------
# ensure_bucket_exists
# ---------------------------------------------------------------------------


def test_ensure_bucket_exists_noop_when_exists(s3_manager: S3Manager) -> None:
    """No-op when bucket already exists."""
    s3_manager._client.head_bucket.return_value = {}

    s3_manager.ensure_bucket_exists()

    s3_manager._client.head_bucket.assert_called_once_with(Bucket="test-backups")
    s3_manager._client.create_bucket.assert_not_called()


def test_ensure_bucket_exists_creates_on_404(s3_manager: S3Manager) -> None:
    """Creates bucket when head_bucket returns 404."""
    s3_manager._client.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")

    s3_manager.ensure_bucket_exists()

    s3_manager._client.create_bucket.assert_called_once_with(Bucket="test-backups")


def test_ensure_bucket_exists_ignores_already_owned(s3_manager: S3Manager) -> None:
    """Ignores BucketAlreadyOwnedByYou race condition."""
    s3_manager._client.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")
    s3_manager._client.create_bucket.side_effect = ClientError(
        {"Error": {"Code": "BucketAlreadyOwnedByYou"}}, "CreateBucket"
    )

    s3_manager.ensure_bucket_exists()  # Should not raise


# ---------------------------------------------------------------------------
# upload_file / download_file
# ---------------------------------------------------------------------------


def test_upload_file(s3_manager: S3Manager, tmp_path: Path) -> None:
    local_file = tmp_path / "dump.sql.gz"
    local_file.write_text("data")

    s3_manager.upload_file(local_file, "2026/dump.sql.gz")

    s3_manager._client.upload_file.assert_called_once_with(str(local_file), "test-backups", "2026/dump.sql.gz")


def test_download_file(s3_manager: S3Manager, tmp_path: Path) -> None:
    dest = tmp_path / "sub" / "dump.sql.gz"

    s3_manager.download_file("2026/dump.sql.gz", dest)

    assert dest.parent.exists()
    s3_manager._client.download_file.assert_called_once_with("test-backups", "2026/dump.sql.gz", str(dest))


# ---------------------------------------------------------------------------
# file_exists
# ---------------------------------------------------------------------------


def test_file_exists_true(s3_manager: S3Manager) -> None:
    s3_manager._client.head_object.return_value = {}

    assert s3_manager.file_exists("some/key") is True


def test_file_exists_false_on_404(s3_manager: S3Manager) -> None:
    s3_manager._client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")

    assert s3_manager.file_exists("missing/key") is False


# ---------------------------------------------------------------------------
# list_prefixes / count_objects / delete_recursive
# ---------------------------------------------------------------------------


def test_list_prefixes(s3_manager: S3Manager) -> None:
    s3_manager._client.get_paginator.return_value.paginate.return_value = [
        {"CommonPrefixes": [{"Prefix": "a/"}, {"Prefix": "b/"}]}
    ]

    result = s3_manager.list_prefixes()

    assert result == ["a", "b"]


def test_count_objects(s3_manager: S3Manager) -> None:
    s3_manager._client.get_paginator.return_value.paginate.return_value = [
        {"KeyCount": 3},
        {"KeyCount": 2},
    ]

    assert s3_manager.count_objects("prefix/") == 5


def test_delete_recursive(s3_manager: S3Manager) -> None:
    s3_manager._client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{"Key": "prefix/a"}, {"Key": "prefix/b"}]}
    ]

    s3_manager.delete_recursive("prefix/")

    s3_manager._client.delete_objects.assert_called_once_with(
        Bucket="test-backups",
        Delete={"Objects": [{"Key": "prefix/a"}, {"Key": "prefix/b"}]},
    )
