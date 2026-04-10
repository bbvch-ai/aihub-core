from enum import StrEnum

from pydantic import BaseModel

BACKUP_SERVICES: tuple[str, ...] = ("PostgreSQL", "Milvus", "Neo4j", "ClickHouse", "Valkey", "NATS")

TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
TIMESTAMP_LENGTH = 19  # len("YYYY-MM-DD_HH-MM-SS")

SERVICE_TO_ASSET_KEY: dict[str, str] = {
    "PostgreSQL": "postgres_backup",
    "Milvus": "milvus_backup",
    "Neo4j": "neo4j_backup",
    "ClickHouse": "clickhouse_backup",
    "Valkey": "valkey_backup",
    "NATS": "nats_backup",
}

if set(SERVICE_TO_ASSET_KEY.keys()) != set(BACKUP_SERVICES):
    raise ValueError(
        f"SERVICE_TO_ASSET_KEY keys {set(SERVICE_TO_ASSET_KEY.keys())} != BACKUP_SERVICES {set(BACKUP_SERVICES)}"
    )


class ServiceStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ServiceResult(BaseModel):
    name: str
    status: ServiceStatus
    duration_seconds: float = 0.0
    error: str | None = None


class BackupSummary(BaseModel):
    timestamp: str
    results: list[ServiceResult]
    total_duration_seconds: float
    retention_warning: str | None = None


class BackupEntry(BaseModel):
    prefix: str
    file_count: int
