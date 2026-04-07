from enum import StrEnum

from pydantic import BaseModel

BACKUP_SERVICES: tuple[str, ...] = ("PostgreSQL", "Milvus", "Neo4j", "ClickHouse", "Valkey", "NATS")

TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"
TIMESTAMP_LENGTH = 19  # len("YYYY-MM-DD_HH-MM-SS")


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
