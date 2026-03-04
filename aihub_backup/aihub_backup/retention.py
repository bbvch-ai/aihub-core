import logging
from datetime import UTC, datetime, timedelta

from aihub_backup.s3 import BACKUP_PREFIX_RE, S3Manager

logger = logging.getLogger(__name__)


class RetentionService:
    @staticmethod
    def run(s3: S3Manager, retention_days: int, minimum_keep: int = 3) -> None:
        if retention_days <= 0:
            logger.info("Retention disabled (BACKUP_RETENTION_DAYS=%d)", retention_days)
            return

        cutoff_date = (datetime.now(UTC) - timedelta(days=retention_days)).strftime("%Y-%m-%d")
        logger.info("Retention: %d days (cutoff: %s, minimum_keep: %d)", retention_days, cutoff_date, minimum_keep)

        prefixes = s3.list_prefixes()
        valid_prefixes = sorted(p for p in prefixes if BACKUP_PREFIX_RE.match(p))

        expired = [p for p in valid_prefixes if p[:10] < cutoff_date]

        remaining_after_delete = len(valid_prefixes) - len(expired)
        if remaining_after_delete < minimum_keep:
            safe_to_delete = len(valid_prefixes) - minimum_keep
            if safe_to_delete <= 0:
                logger.warning(
                    "Retention: keeping all %d backup(s) (minimum_keep=%d)", len(valid_prefixes), minimum_keep
                )
                expired = []
            else:
                expired = sorted(expired)[:safe_to_delete]

        expired_set = set(expired)

        for prefix in valid_prefixes:
            if prefix in expired_set:
                logger.info("  Deleting: %s (%s)", prefix, prefix[:10])
                s3.delete_recursive(prefix + "/")

        logger.info("Retention cleanup: done")
