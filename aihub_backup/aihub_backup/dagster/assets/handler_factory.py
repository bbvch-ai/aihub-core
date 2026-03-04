import inspect

from aihub_backup.docker_client import DockerManager
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.services.clickhouse import ClickHouseHandler
from aihub_backup.services.milvus import MilvusHandler
from aihub_backup.services.nats import NatsHandler
from aihub_backup.services.neo4j import Neo4jHandler
from aihub_backup.services.postgres import PostgresHandler
from aihub_backup.services.valkey import ValkeyHandler
from aihub_backup.settings import BackupSettings

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
