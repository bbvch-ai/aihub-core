from unittest.mock import MagicMock

from aihub_backup.retention import run_retention


def test_retention_deletes_old_online_backups() -> None:
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2026-01-01_02-00-00_online",
        "2026-02-17_02-00-00_online",
        "2026-02-18_02-00-00_online",
    ]

    # With 7 day retention, the Jan 1st backup should be deleted
    # (assuming current date is around Feb 18, 2026)
    run_retention(s3, retention_days=7)

    # The old backup should have been deleted
    s3.delete_recursive.assert_called_once_with("2026-01-01_02-00-00_online/")


def test_retention_preserves_offline_backups() -> None:
    s3 = MagicMock()
    s3.list_prefixes.return_value = [
        "2020-01-01_02-00-00_offline",  # Very old but offline
        "2026-02-18_02-00-00_online",
    ]

    run_retention(s3, retention_days=7)

    # Offline backups are never deleted
    s3.delete_recursive.assert_not_called()


def test_retention_disabled_when_zero() -> None:
    s3 = MagicMock()
    run_retention(s3, retention_days=0)
    s3.list_prefixes.assert_not_called()
