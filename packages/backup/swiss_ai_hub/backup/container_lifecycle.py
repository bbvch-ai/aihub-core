import logging
from collections.abc import Sequence

from pydantic import BaseModel

from swiss_ai_hub.backup.docker_client import DockerManager
from swiss_ai_hub.backup.models import BACKUP_SERVICES

logger = logging.getLogger(__name__)

LOG_SEPARATOR = "=" * 44


class ServiceDeps(BaseModel, frozen=True):
    """Containers a backup/restore handler needs running (or stopped for offline handlers)."""

    containers: tuple[str, ...] | None
    timeout: int


SERVICE_DEPS: dict[str, ServiceDeps] = {
    "PostgreSQL": ServiceDeps(containers=("postgres", "postgres-ferretdb"), timeout=60),
    "Neo4j": ServiceDeps(containers=None, timeout=0),
    "ClickHouse": ServiceDeps(containers=("clickhouse",), timeout=60),
    "Valkey": ServiceDeps(containers=("valkey",), timeout=60),
    "NATS": ServiceDeps(containers=("nats",), timeout=60),
    "Milvus": ServiceDeps(containers=("milvus",), timeout=180),
}

if set(SERVICE_DEPS.keys()) != set(BACKUP_SERVICES):
    raise ValueError(
        f"SERVICE_DEPS and BACKUP_SERVICES must contain the same entries: "
        f"only in SERVICE_DEPS={set(SERVICE_DEPS.keys()) - set(BACKUP_SERVICES)}, "
        f"only in BACKUP_SERVICES={set(BACKUP_SERVICES) - set(SERVICE_DEPS.keys())}"
    )


def _assert_no_overlapping_deps(deps: dict[str, ServiceDeps]) -> None:
    """Parallel backup requires disjoint container deps across handlers."""
    seen: dict[str, str] = {}
    for service, dep in deps.items():
        if dep.containers is None:
            continue
        for container in dep.containers:
            if container in seen:
                raise ValueError(
                    f"Container '{container}' claimed by both '{seen[container]}' "
                    f"and '{service}'. Parallel backup requires disjoint deps."
                )
            seen[container] = service


_assert_no_overlapping_deps(SERVICE_DEPS)


class ContainerLifecycleManager:
    def __init__(self, docker: DockerManager) -> None:
        self._docker = docker

    def stop_containers(self, label: str, containers: Sequence[str], timeout: int = 30) -> None:
        logger.info("Stopping %s...", label)
        for name in containers:
            if self._docker.stop_container(name, timeout=timeout):
                logger.info("  Stopped: %s", name)

    def start_and_await_healthy(
        self,
        containers: Sequence[str],
        timeout: int = 120,
        label: str | None = None,
    ) -> None:
        if label:
            logger.info("Starting %s...", label)
        existing = [name for name in containers if self._docker.container_exists(name)]
        for name in existing:
            self._docker.start_container(name)
        failed = [name for name in existing if not self._docker.wait_for_healthy(name, timeout)]
        if failed:
            raise RuntimeError(f"Containers failed health check: {', '.join(failed)}")
