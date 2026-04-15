import logging
import re
from typing import override

import clickhouse_connect

from swiss_ai_hub.backup.s3 import S3Manager
from swiss_ai_hub.backup.services.base import BackupHandler
from swiss_ai_hub.backup.settings import BackupSettings

logger = logging.getLogger(__name__)

_BACKUP_NAME_RE = re.compile(r"^backup_[a-zA-Z0-9_]+$")
_TABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

_BACKUP_TIMEOUT = 3600


class ClickHouseHandler(BackupHandler):
    def __init__(self, settings: BackupSettings, s3: S3Manager) -> None:
        self._settings = settings
        self._s3 = s3

    @property
    @override
    def service_name(self) -> str:
        return "ClickHouse"

    @override
    def backup(self, backup_id: str, s3_prefix: str) -> None:
        validated_name = self._validated_backup_name_or_raise(f"backup_{backup_id.replace('-', '_')}")

        client = self._create_client()
        self._validate_reachable_or_raise(client)

        disk_path = f"{s3_prefix}/clickhouse/{validated_name}/"
        logger.info("Creating ClickHouse backup to S3 via named disk...")
        client.command(f"BACKUP DATABASE default TO Disk('backup_s3', '{disk_path}')")
        logger.info("ClickHouse: done")

    @override
    def restore(self, backup_prefix: str) -> None:
        if not self._has_backup_data(backup_prefix):
            logger.info("No ClickHouse backup in %s, skipping", backup_prefix)
            return

        client = self._create_client()

        logger.info("Dropping existing tables before restore...")
        self._drop_existing_tables(client)

        disk_path = self._find_backup_disk_path(backup_prefix)
        logger.info("Restoring ClickHouse from S3 via named disk...")
        client.command(f"RESTORE DATABASE default FROM Disk('backup_s3', '{disk_path}')")
        logger.info("ClickHouse restore complete")

    def _has_backup_data(self, backup_prefix: str) -> bool:
        prefixes = self._s3.list_prefixes(f"{backup_prefix}/clickhouse/")
        return any("backup_" in p for p in prefixes)

    def _find_backup_disk_path(self, backup_prefix: str) -> str:
        backup_name = f"backup_{backup_prefix.replace('-', '_')}"
        validated_name = self._validated_backup_name_or_raise(backup_name)
        return f"{backup_prefix}/clickhouse/{validated_name}/"

    @staticmethod
    def _validated_backup_name_or_raise(name: str) -> str:
        if not _BACKUP_NAME_RE.match(name):
            raise ValueError(f"Invalid ClickHouse backup name: {name!r}")
        return name

    def _create_client(self) -> clickhouse_connect.driver.Client:
        return clickhouse_connect.get_client(
            host=self._settings.CLICKHOUSE_HOST,
            port=self._settings.CLICKHOUSE_PORT,
            username=self._settings.CLICKHOUSE_USER,
            password=self._settings.LANGFUSE_CLICKHOUSE_PASSWORD.get_secret_value(),
            send_receive_timeout=_BACKUP_TIMEOUT,
        )

    @staticmethod
    def _validate_reachable_or_raise(client: clickhouse_connect.driver.Client) -> None:
        client.command("SELECT 1")

    @staticmethod
    def _list_user_tables(client: clickhouse_connect.driver.Client) -> list[str]:
        result = client.query(
            "SELECT name FROM system.tables WHERE database = 'default' AND engine NOT IN ('View', 'MaterializedView')"
        )
        return [row[0] for row in result.result_rows]

    def _drop_existing_tables(self, client: clickhouse_connect.driver.Client) -> None:
        tables = self._list_user_tables(client)
        for table_name in tables:
            if not _TABLE_NAME_RE.match(table_name):
                logger.warning("Skipping table with invalid name: %r", table_name)
                continue
            logger.info("  Dropping table: %s", table_name)
            client.command(f"DROP TABLE IF EXISTS default.`{table_name}`")
