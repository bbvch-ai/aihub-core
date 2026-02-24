from typing import Literal, get_args

import dagster as dg

from aihub_backup.models import BACKUP_SERVICES


class BackupConfig(dg.Config):
    mode: Literal["online", "offline"] = "online"


class RestoreConfig(dg.Config):
    """
    When timestamp is None, the latest backup is auto-selected.
    When force=True, restore continues past individual service failures.
    """

    timestamp: str | None = None
    force: bool = False


_SERVICE_LITERAL = Literal["PostgreSQL", "Milvus", "Neo4j", "ClickHouse", "Valkey", "NATS"]
if set(get_args(_SERVICE_LITERAL)) != set(BACKUP_SERVICES):
    raise ValueError(
        f"_SERVICE_LITERAL args {set(get_args(_SERVICE_LITERAL))} != BACKUP_SERVICES {set(BACKUP_SERVICES)}"
    )


class SingleServiceRestoreConfig(dg.Config):
    service_name: _SERVICE_LITERAL
    timestamp: str | None = None
