import logging
import socket

import docker
from docker.errors import NotFound
from docker.models.containers import Container

logger = logging.getLogger(__name__)

_EXCLUDE_PREFIXES = ("backup-", "seaweedfs-", "etcd")


class ContainerDiscovery:
    """Discovers platform containers using the built-in Docker Compose project label.

    No custom labels needed — Docker Compose automatically adds
    ``com.docker.compose.project`` to every container it creates.
    """

    PROJECT_LABEL = "com.docker.compose.project"

    def __init__(self) -> None:
        self._client = docker.from_env(timeout=30)
        self._project = self._detect_project()

    def discover_managed_containers(self) -> list[str]:
        """Return names of all containers in the compose project, excluding infrastructure."""
        containers = self._client.containers.list(
            all=True,
            filters={"label": f"{self.PROJECT_LABEL}={self._project}"},
        )
        managed = [c.name for c in containers if c.name and not self._is_excluded(c.name)]
        logger.info(
            "Discovered %d managed containers (project=%s): %s",
            len(managed),
            self._project,
            ", ".join(sorted(managed)),
        )
        return managed

    def stop_all_managed(self) -> list[str]:
        """Stop all managed containers, return names of those that were running."""
        containers = self._client.containers.list(
            all=True,
            filters={"label": f"{self.PROJECT_LABEL}={self._project}"},
        )
        previously_running: list[str] = []
        for container in containers:
            name = container.name
            if not name or self._is_excluded(name):
                continue
            if container.status == "running":
                previously_running.append(name)
                logger.info("Stopping: %s (timeout=30s)...", name)
                container.stop(timeout=30)
                logger.info("Stopped: %s", name)

        logger.info("Stopped %d containers", len(previously_running))
        return previously_running

    def start_all(self, containers: list[str]) -> None:
        """Start all named containers (best-effort, no dependency ordering).

        Docker Compose ``restart: always/unless-stopped`` policies ensure
        services that crash on first start (because a dependency isn't ready
        yet) will be automatically restarted until they converge.
        """
        logger.info("Restarting %d containers...", len(containers))
        for name in containers:
            try:
                container: Container = self._client.containers.get(name)
                if container.status != "running":
                    logger.info("Starting: %s...", name)
                    container.start()
                    logger.info("Started: %s", name)
            except NotFound:
                logger.warning("Container %s no longer exists, skipping restart", name)

    def _detect_project(self) -> str:
        hostname = socket.gethostname()
        logger.info("Detecting compose project from hostname: %s", hostname)
        try:
            self_container: Container = self._client.containers.get(hostname)
            project: str = self_container.labels.get(self.PROJECT_LABEL, "")
            if not project:
                raise RuntimeError(
                    f"Container {hostname} has no {self.PROJECT_LABEL} label. "
                    "Is the backup running inside Docker Compose?"
                )
            logger.info("Detected compose project: %s", project)
            return project
        except NotFound as e:
            raise RuntimeError(
                f"Could not find own container by hostname '{hostname}'. Is Docker socket mounted?"
            ) from e

    @staticmethod
    def _is_excluded(name: str) -> bool:
        return any(name.startswith(prefix) for prefix in _EXCLUDE_PREFIXES)
