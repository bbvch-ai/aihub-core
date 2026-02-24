import logging
from datetime import UTC, datetime, timedelta

from aihub_backup.s3 import BACKUP_PREFIX_RE, S3Manager

logger = logging.getLogger(__name__)


def run_retention(s3: S3Manager, retention_days: int) -> None:
    """Offline backups are never auto-deleted (preserved indefinitely)."""
    if retention_days <= 0:
        logger.info("Retention disabled (BACKUP_RETENTION_DAYS=%d)", retention_days)
        return

    cutoff_date = (datetime.now(UTC) - timedelta(days=retention_days)).strftime("%Y-%m-%d")
    logger.info("Retention: %d days (cutoff: %s)", retention_days, cutoff_date)

    prefixes = s3.list_prefixes()
    for prefix in prefixes:
        if not BACKUP_PREFIX_RE.match(prefix):
            continue

        # ISO date prefixes (YYYY-MM-DD) support lexicographic comparison
        backup_date = prefix[:10]

        if prefix.endswith("_offline"):
            logger.info("  Keeping: %s (offline - preserved indefinitely)", prefix)
            continue

        if backup_date < cutoff_date:
            logger.info("  Deleting: %s (%s)", prefix, backup_date)
            s3.delete_recursive(prefix + "/")

    logger.info("Retention cleanup: done")
