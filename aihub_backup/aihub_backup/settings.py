from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupSettings(BaseSettings):
    """No env_prefix — env var names match docker-compose exactly."""

    model_config = SettingsConfigDict()

    BACKUP_RETENTION_DAYS: Annotated[int, Field(ge=0)] = 7
    BACKUP_SKIP_MILVUS_ONLINE: bool = False
    BACKUP_SKIP_MILVUS_OFFLINE: bool = False

    POSTGRES_HOST: str = "postgres"
    POSTGRES_USER: str = "admin"
    PGPASSWORD: SecretStr

    POSTGRES_FERRETDB_HOST: str = "postgres-ferretdb"
    POSTGRES_FERRETDB_USER: str = "admin"
    PGPASSWORD_FERRETDB: SecretStr

    MILVUS_HOST: str = "milvus-standalone"
    MILVUS_PORT: Annotated[int, Field(gt=0)] = 19530
    MILVUS_ROOT_PASSWORD: SecretStr

    NEO4J_CONTAINER: str = "neo4j"

    CLICKHOUSE_HOST: str = "clickhouse"
    CLICKHOUSE_USER: str = "clickhouse"
    CLICKHOUSE_PASSWORD: SecretStr

    # "Redis-compatible" — clarifies why the token is named REDIS_TOKEN
    VALKEY_CONTAINER: str = "valkey"
    REDIS_TOKEN: SecretStr

    NATS_URL: str = "nats://nats:4222"
    NATS_TOKEN: SecretStr

    AWS_ACCESS_KEY_ID: str = "admin"
    AWS_SECRET_ACCESS_KEY: SecretStr
    AWS_ENDPOINT_URL: str = "http://seaweedfs-s3:9000"
    BACKUP_S3_BUCKET: str = "backups"
