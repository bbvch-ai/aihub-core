from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from aihub_backup.retention import RetentionService

FROZEN_NOW = datetime(2026, 2, 18, 12, 0, 0, tzinfo=UTC)


def test_retention_deletes_old_backups() -> None:
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-01-01_02-00-00",
        "2026-02-15_02-00-00",
        "2026-02-16_02-00-00",
        "2026-02-17_02-00-00",
        "2026-02-18_02-00-00",
    ]

    with patch("aihub_backup.retention.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        RetentionService.run(s3, retention_days=7)

    s3.delete_recursive.assert_called_once_with("2026-01-01_02-00-00/")


def test_retention_disabled_when_zero() -> None:
    s3 = MagicMock()
    RetentionService.run(s3, retention_days=0)
    s3.list_prefixes.assert_not_called()


def test_retention_keeps_backup_on_exact_cutoff_date() -> None:
    """Backups dated exactly retention_days ago are kept (strict < comparison)."""
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-02-11_02-00-00",
    ]

    with patch("aihub_backup.retention.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        RetentionService.run(s3, retention_days=7)

    s3.delete_recursive.assert_not_called()


def test_retention_minimum_keep_prevents_total_wipe() -> None:
    """When all backups are expired, minimum_keep prevents deleting all of them."""
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-01-01_02-00-00",
        "2026-01-02_02-00-00",
    ]

    with patch("aihub_backup.retention.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        RetentionService.run(s3, retention_days=7, minimum_keep=3)

    s3.delete_recursive.assert_not_called()


def test_retention_minimum_keep_allows_partial_deletion() -> None:
    """When enough backups remain after deletion, expired ones are still removed."""
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-01-01_02-00-00",
        "2026-01-05_02-00-00",
        "2026-02-15_02-00-00",
        "2026-02-16_02-00-00",
        "2026-02-17_02-00-00",
    ]

    with patch("aihub_backup.retention.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        RetentionService.run(s3, retention_days=7, minimum_keep=3)

    assert s3.delete_recursive.call_count == 2
    s3.delete_recursive.assert_any_call("2026-01-01_02-00-00/")
    s3.delete_recursive.assert_any_call("2026-01-05_02-00-00/")


def test_retention_minimum_keep_one_protects_last_backup() -> None:
    """minimum_keep=1 protects the last remaining backup."""
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-01-01_02-00-00",
    ]

    with patch("aihub_backup.retention.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        RetentionService.run(s3, retention_days=7, minimum_keep=1)

    s3.delete_recursive.assert_not_called()


def test_retention_minimum_keep_partial_when_close_to_limit() -> None:
    """When deleting all expired would violate minimum_keep, only delete oldest ones."""
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-01-01_02-00-00",
        "2026-01-02_02-00-00",
        "2026-01-03_02-00-00",
        "2026-02-17_02-00-00",
    ]

    with patch("aihub_backup.retention.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        RetentionService.run(s3, retention_days=7, minimum_keep=3)

    # 4 backups, 3 expired, minimum_keep=3 -> can only delete 1
    assert s3.delete_recursive.call_count == 1
    s3.delete_recursive.assert_called_once_with("2026-01-01_02-00-00/")


def test_retention_minimum_keep_exact_boundary_deletes_nothing() -> None:
    """When total backups == minimum_keep and all expired, nothing is deleted."""
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-01-01_02-00-00",
        "2026-01-02_02-00-00",
        "2026-01-03_02-00-00",
    ]

    with patch("aihub_backup.retention.datetime") as mock_dt:
        mock_dt.now.return_value = FROZEN_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        RetentionService.run(s3, retention_days=7, minimum_keep=3)

    s3.delete_recursive.assert_not_called()
