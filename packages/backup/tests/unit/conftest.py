import pytest
from pydantic import SecretStr

from swiss_ai_hub.backup.settings import BackupSettings


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
        S3_BUCKET="test-backups",
        RETENTION_DAYS=7,
    )
