from swiss_ai_hub.backup.docker_client import DockerManager
from swiss_ai_hub.backup.s3 import S3Manager
from swiss_ai_hub.backup.services.base import BackupHandler
from swiss_ai_hub.backup.services.stubs import (
    ClickHouseHandler,
    MilvusHandler,
    NatsHandler,
    Neo4jHandler,
    PostgresHandler,
)
from swiss_ai_hub.backup.services.valkey import ValkeyHandler
from swiss_ai_hub.backup.settings import BackupSettings

HANDLER_FACTORIES: dict[str, type[BackupHandler]] = {
    "PostgreSQL": PostgresHandler,
    "Milvus": MilvusHandler,
    "Neo4j": Neo4jHandler,
    "ClickHouse": ClickHouseHandler,
    "Valkey": ValkeyHandler,
    "NATS": NatsHandler,
}


def create_handler(
    service_name: str,
    settings: BackupSettings,
    s3: S3Manager,
    docker: DockerManager,
) -> BackupHandler:
    handler_class = HANDLER_FACTORIES[service_name]
    return handler_class(settings, s3, docker)  # type: ignore[call-arg]
