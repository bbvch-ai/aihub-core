import logging
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

import docker
from docker.errors import NotFound
from docker.models.containers import Container

logger = logging.getLogger(__name__)

_EXCLUDE_PREFIXES = ("backup-", "seaweedfs-", "etcd", "traefik", "oauth2proxy-")


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
        """Stop all managed containers in parallel, return names of those that were running."""
        containers = self._client.containers.list(
            all=True,
            filters={"label": f"{self.PROJECT_LABEL}={self._project}"},
        )
        to_stop: list[tuple[str, Container]] = []
        for container in containers:
            name = container.name
            if not name or self._is_excluded(name):
                continue
            if container.status == "running":
                to_stop.append((name, container))

        logger.info("Stopping %d containers in parallel...", len(to_stop))

        def _stop(name: str, container: Container) -> str:
            logger.info("Stopping: %s (timeout=30s)...", name)
            container.stop(timeout=30)
            logger.info("Stopped: %s", name)
            return name

        previously_running: list[str] = []
        with ThreadPoolExecutor(max_workers=len(to_stop) or 1) as pool:
            futures = {pool.submit(_stop, name, c): name for name, c in to_stop}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    previously_running.append(future.result())
                except Exception:
                    logger.exception("Failed to stop container %s, it may still be running", name)

        logger.info("Successfully stopped %d containers", len(previously_running))
        return previously_running

    def start_all(self, container_names: list[str]) -> None:
        """Start all named containers in parallel (best-effort, no dependency ordering).

        Docker Compose ``restart: always/unless-stopped`` policies ensure
        services that crash on first start (because a dependency isn't ready
        yet) will be automatically restarted until they converge.
        """
        logger.info("Starting %d containers in parallel...", len(container_names))

        def _start(name: str) -> None:
            try:
                container: Container = self._client.containers.get(name)
                if container.status != "running":
                    logger.info("Starting: %s...", name)
                    container.start()
                    logger.info("Started: %s", name)
            except NotFound:
                logger.warning("Container %s no longer exists, skipping", name)

        with ThreadPoolExecutor(max_workers=len(container_names) or 1) as pool:
            list(pool.map(_start, container_names))

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
