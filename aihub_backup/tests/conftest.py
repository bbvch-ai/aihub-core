import pytest
from pydantic import SecretStr

from aihub_backup.dagster.resources import (
    BackupHandlersResource,
    BackupSettingsResource,
    DockerManagerResource,
    S3ManagerResource,
)
from aihub_backup.settings import BackupSettings


@pytest.fixture
def settings() -> BackupSettings:
    return BackupSettings(
        POSTGRES_HOST="localhost",
        POSTGRES_USER="test",
        PGPASSWORD=SecretStr("testpass"),
        POSTGRES_FERRETDB_HOST="localhost",
        POSTGRES_FERRETDB_USER="test",
        PGPASSWORD_FERRETDB=SecretStr("testpass"),
        MILVUS_HOST="localhost",
        MILVUS_PORT=19530,
        MILVUS_ROOT_PASSWORD=SecretStr("testpass"),
        NEO4J_CONTAINER="neo4j",
        CLICKHOUSE_HOST="clickhouse",
        CLICKHOUSE_USER="clickhouse",
        CLICKHOUSE_PASSWORD=SecretStr("testpass"),
        VALKEY_CONTAINER="valkey",
        REDIS_TOKEN=SecretStr("testpass"),
        NATS_URL="nats://localhost:4222",
        NATS_TOKEN=SecretStr("testpass"),
        AWS_ACCESS_KEY_ID="test",
        AWS_SECRET_ACCESS_KEY=SecretStr("testpass"),
        AWS_ENDPOINT_URL="http://localhost:9000",
        BACKUP_S3_BUCKET="test-backups",
        BACKUP_RETENTION_DAYS=7,
    )


@pytest.fixture
def dagster_resources() -> dict[str, object]:
    """Dagster resource dict shared across asset and ops tests."""
    return {
        "backup_settings": BackupSettingsResource(),
        "s3_manager": S3ManagerResource(settings=BackupSettingsResource()),
        "docker_manager": DockerManagerResource(),
        "backup_handlers": BackupHandlersResource(
            settings=BackupSettingsResource(),
            s3=S3ManagerResource(settings=BackupSettingsResource()),
            docker=DockerManagerResource(),
        ),
    }
