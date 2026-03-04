import pytest
from pydantic import SecretStr

from aihub_backup.dagster.resources.BackupSettingsResource import BackupSettingsResource
from aihub_backup.dagster.resources.ContainerDiscoveryResource import ContainerDiscoveryResource
from aihub_backup.dagster.resources.ContainerLifecycleResource import ContainerLifecycleResource
from aihub_backup.dagster.resources.DockerManagerResource import DockerManagerResource
from aihub_backup.dagster.resources.S3ManagerResource import S3ManagerResource
from aihub_backup.settings import BackupSettings


@pytest.fixture
def settings() -> BackupSettings:
    return BackupSettings(
        POSTGRES_HOST="localhost",
        POSTGRES_USER="test",
        POSTGRES_PASSWORD=SecretStr("testpass"),
        POSTGRES_FERRETDB_HOST="localhost",
        MONGO_USERNAME="test",
        MONGO_PASSWORD=SecretStr("testpass"),
        MILVUS_HOST="localhost",
        MILVUS_PORT=19530,
        MILVUS_ROOT_PASSWORD=SecretStr("testpass"),
        NEO4J_CONTAINER="neo4j",
        CLICKHOUSE_HOST="clickhouse",
        CLICKHOUSE_PORT=8123,
        CLICKHOUSE_USER="clickhouse",
        LANGFUSE_CLICKHOUSE_PASSWORD=SecretStr("testpass"),
        VALKEY_HOST="valkey",
        VALKEY_PORT=6379,
        VALKEY_CONTAINER="valkey",
        REDIS_TOKEN=SecretStr("testpass"),
        NATS_URL="nats://localhost:4222",
        NATS_TOKEN=SecretStr("testpass"),
        S3_STORAGE_ACCESS_KEY="test",
        S3_STORAGE_SECRET_KEY=SecretStr("testpass"),
        AWS_ENDPOINT_URL="http://localhost:9000",
        BACKUP_S3_BUCKET="test-backups",
        BACKUP_RETENTION_DAYS=7,
    )


@pytest.fixture
def dagster_resources() -> dict[str, object]:
    """Dagster resource dict shared across asset and ops tests."""
    settings = BackupSettingsResource()
    docker = DockerManagerResource()
    return {
        "backup_settings": settings,
        "s3_manager": S3ManagerResource(settings=settings),
        "docker_manager": docker,
        "container_lifecycle": ContainerLifecycleResource(docker=docker),
        "container_discovery": ContainerDiscoveryResource(),
    }
