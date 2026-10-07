from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupSettings(BaseSettings):
    """All env vars are prefixed with ``BACKUP_`` (e.g. ``BACKUP_POSTGRES_HOST``).

    Field names omit the prefix — pydantic prepends it via ``env_prefix``.
    Don't add a ``BACKUP_`` to a field name; that would read ``BACKUP_BACKUP_*``.
    """

    model_config = SettingsConfigDict(env_prefix="BACKUP_")

    RETENTION_DAYS: Annotated[int, Field(ge=0)] = 7
    MINIMUM_KEEP: Annotated[int, Field(ge=1)] = 3

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: Annotated[int, Field(gt=0)] = 5432
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: SecretStr

    POSTGRES_FERRETDB_HOST: str = "postgres-ferretdb"
    MONGO_USERNAME: str = "admin"
    MONGO_PASSWORD: SecretStr

    # Subprocess timeout (seconds) for pg_dump / pg_restore / psql. Default 6h
    # accommodates large dagster DBs (>100GB) where the previous 5min cap was
    # impossible to meet. Operators with smaller deployments can lower this.
    POSTGRES_SUBPROCESS_TIMEOUT_SECONDS: Annotated[int, Field(gt=0)] = 21_600

    MILVUS_HOST: str = "milvus-standalone"
    MILVUS_PORT: Annotated[int, Field(gt=0)] = 19530
    MILVUS_ROOT_PASSWORD: SecretStr

    NEO4J_CONTAINER: str = "neo4j"

    CLICKHOUSE_HOST: str = "clickhouse"
    CLICKHOUSE_PORT: Annotated[int, Field(gt=0)] = 8123
    CLICKHOUSE_USER: str = "clickhouse"
    LANGFUSE_CLICKHOUSE_PASSWORD: SecretStr

    VALKEY_HOST: str = "valkey"
    VALKEY_PORT: Annotated[int, Field(gt=0)] = 6379
    VALKEY_CONTAINER: str = "valkey"
    REDIS_TOKEN: SecretStr

    NATS_URL: str = "nats://nats:4222"
    NATS_TOKEN: SecretStr

    S3_STORAGE_ACCESS_KEY: str = "admin"
    S3_STORAGE_SECRET_KEY: SecretStr
    AWS_ENDPOINT_URL: str = "http://seaweedfs-s3:9000"
    S3_BUCKET: str = "backups"

    # Maintenance subsystem — Postgres health for the dagster DB. The
    # maintenance code location runs alongside the backup code in the same
    # backup Dagster instance. See packages/backup/CLAUDE.md.
    DAGSTER_DB: str = "dagster"

    # Retention windows for the dagster_cleanup_job. Defaults follow the official
    # Dagster database-tuning recipe.
    DAGSTER_DEBUG_LOG_RETENTION_DAYS: Annotated[int, Field(ge=0)] = 7
    DAGSTER_INFO_LOG_RETENTION_DAYS: Annotated[int, Field(ge=0)] = 60
    DAGSTER_WARNING_LOG_RETENTION_DAYS: Annotated[int, Field(ge=0)] = 60
    DAGSTER_UNIMPORTANT_EVENT_RETENTION_DAYS: Annotated[int, Field(ge=0)] = 30

    # Cap rows per DELETE so first run on a backlogged DB does not flood WAL.
    DAGSTER_CLEANUP_BATCH_LIMIT: Annotated[int, Field(gt=0)] = 1_000_000

    # Kill switch — set to true to make the maintenance schedules a no-op
    # (operators can vet the jobs before letting them run).
    MAINTENANCE_DISABLED: bool = False
