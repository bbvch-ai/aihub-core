import dagster as dg

from aihub_backup.docker_client import DockerManager
from aihub_backup.models import BACKUP_SERVICES
from aihub_backup.orchestrator import Orchestrator
from aihub_backup.s3 import S3Manager
from aihub_backup.services.base import BackupHandler
from aihub_backup.services.clickhouse import ClickHouseHandler
from aihub_backup.services.milvus import MilvusHandler
from aihub_backup.services.nats import NatsHandler
from aihub_backup.services.neo4j import Neo4jHandler
from aihub_backup.services.postgres import PostgresHandler
from aihub_backup.services.valkey import ValkeyHandler
from aihub_backup.settings import BackupSettings


class BackupSettingsResource(dg.ConfigurableResource):
    """
    Wraps BackupSettings (Pydantic BaseSettings) as a Dagster resource so
    it can be injected into ops/assets and swapped with mocks in tests.
    """

    def create_settings(self) -> BackupSettings:
        return BackupSettings()  # type: ignore[call-arg]


class S3ManagerResource(dg.ConfigurableResource):
    """
    Enables Dagster dependency injection and allows tests to substitute
    a mock S3Manager without touching real S3/SeaweedFS endpoints.
    """

    settings: BackupSettingsResource

    def create_s3_manager(self, settings: BackupSettings | None = None) -> S3Manager:
        s3 = S3Manager(settings or self.settings.create_settings())
        s3.ensure_bucket_exists()
        return s3


class DockerManagerResource(dg.ConfigurableResource):
    """
    Wraps DockerManager for Dagster resource injection, allowing tests
    to mock Docker SDK interactions without a live Docker daemon.
    """

    def create_docker_manager(self) -> DockerManager:
        return DockerManager()


class BackupHandlersResource(dg.ConfigurableResource):
    """
    Centralizes handler construction for Dagster injection. Tests can
    mock individual handler dependencies without rebuilding the full graph.
    """

    settings: BackupSettingsResource
    s3: S3ManagerResource
    docker: DockerManagerResource

    def create_handlers(
        self,
        settings: BackupSettings | None = None,
        s3: S3Manager | None = None,
        docker: DockerManager | None = None,
    ) -> list[BackupHandler]:
        resolved_settings = settings or self.settings.create_settings()
        resolved_s3 = s3 or self.s3.create_s3_manager(settings=resolved_settings)
        resolved_docker = docker or self.docker.create_docker_manager()
        handlers: list[BackupHandler] = [
            PostgresHandler(resolved_settings, resolved_s3),
            MilvusHandler(resolved_settings, resolved_s3),
            Neo4jHandler(resolved_settings, resolved_s3, resolved_docker),
            ClickHouseHandler(resolved_settings, resolved_s3, resolved_docker),
            ValkeyHandler(resolved_settings, resolved_s3, resolved_docker),
            NatsHandler(resolved_settings, resolved_s3),
        ]
        handler_names = {h.service_name for h in handlers}
        if handler_names != set(BACKUP_SERVICES):
            raise ValueError(f"Handler mismatch: {handler_names} != {set(BACKUP_SERVICES)}")
        return handlers


def build_orchestrator(
    backup_settings: BackupSettingsResource,
    s3_manager: S3ManagerResource,
    docker_manager: DockerManagerResource,
    backup_handlers: BackupHandlersResource,
) -> tuple[Orchestrator, S3Manager]:
    settings = backup_settings.create_settings()
    s3 = s3_manager.create_s3_manager(settings=settings)
    docker = docker_manager.create_docker_manager()
    handlers = backup_handlers.create_handlers(settings=settings, s3=s3, docker=docker)
    return Orchestrator(settings=settings, s3=s3, docker=docker, handlers=handlers), s3
