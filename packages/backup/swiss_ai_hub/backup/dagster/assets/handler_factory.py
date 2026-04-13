import inspect

from swiss_ai_hub.backup.docker_client import DockerManager
from swiss_ai_hub.backup.s3 import S3Manager
from swiss_ai_hub.backup.services.base import BackupHandler
from swiss_ai_hub.backup.services.postgres import PostgresHandler
from swiss_ai_hub.backup.services.milvus import MilvusHandler
from swiss_ai_hub.backup.services.stubs import (
    ClickHouseHandler,
    NatsHandler,
    Neo4jHandler,
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
    params = inspect.signature(handler_class.__init__).parameters
    needs_docker = any(p.annotation is DockerManager for p in params.values())
    if needs_docker:
        return handler_class(settings, s3, docker)  # type: ignore[call-arg]
    return handler_class(settings, s3)  # type: ignore[call-arg]
