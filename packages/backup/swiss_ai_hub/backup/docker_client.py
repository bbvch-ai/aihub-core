import logging
import tarfile
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import docker
from docker.errors import NotFound
from docker.models.containers import Container

logger = logging.getLogger(__name__)

_TERMINAL_STATES = frozenset({"exited", "dead"})


class DockerManager:
    def __init__(self) -> None:
        self._client = docker.from_env(timeout=300)

    def container_exists(self, name: str) -> bool:
        return self._get_container(name) is not None

    def container_is_running(self, name: str) -> bool:
        container = self._get_container(name)
        if container is None:
            return False
        return container.status == "running"

    def stop_container(self, name: str, timeout: int = 30) -> bool:
        container = self._get_container(name)
        if container is None:
            return False
        if container.status != "running":
            return False
        container.stop(timeout=timeout)
        logger.info("Stopped container: %s", name)
        return True

    def start_container(self, name: str) -> bool:
        container = self._get_container(name)
        if container is None:
            return False
        container.start()
        logger.info("Started container: %s", name)
        return True

    def wait_for_healthy(self, name: str, timeout: int = 120) -> bool:
        container = self._get_container(name)
        if container is None:
            logger.warning("Container %s not found during health check", name)
            return False

        deadline = time.monotonic() + timeout
        started_at = self._parse_started_at(container)

        while time.monotonic() < deadline:
            container.reload()
            container_status = container.attrs.get("State", {}).get("Status", "")
            if container_status in _TERMINAL_STATES:
                logger.warning("%s is in terminal state (status=%s)", name, container_status)
                return False
            if container_status != "running":
                time.sleep(5)
                continue
            health = container.attrs.get("State", {}).get("Health")
            if health is None:
                return True
            if health.get("Status") == "healthy" and self._has_fresh_healthcheck(health, started_at):
                return True
            time.sleep(5)

        logger.warning("%s did not become healthy within %ds", name, timeout)
        return False

    @staticmethod
    def _parse_started_at(container: Container) -> datetime:
        raw = container.attrs.get("State", {}).get("StartedAt", "")
        try:
            ts = datetime.fromisoformat(raw)
            return ts if ts.tzinfo else ts.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=UTC)

    @staticmethod
    def _has_fresh_healthcheck(health: dict[str, Any], started_at: datetime) -> bool:
        """Return True if the latest healthcheck ran after the container started."""
        log = health.get("Log") or []
        if not log:
            return False
        last_end = log[-1].get("End", "")
        try:
            ts = datetime.fromisoformat(last_end)
            check_time = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
            return check_time > started_at
        except (ValueError, TypeError):
            return False

    def get_container_image(self, name: str) -> str | None:
        container = self._get_container(name)
        if container is None or container.image is None:
            return None
        return str(container.image.tags[0]) if container.image.tags else str(container.image.id)

    def get_volume_mount(self, name: str, destination: str) -> str | None:
        container = self._get_container(name)
        if container is None:
            return None
        for mount in container.attrs.get("Mounts", []):
            if mount.get("Destination") == destination:
                return mount.get("Source")  # type: ignore[no-any-return]
        return None

    def exec_in_container(
        self,
        name: str,
        command: str | list[str],
        environment: dict[str, str] | None = None,
    ) -> tuple[int, str]:
        container = self._get_container(name)
        if container is None:
            raise RuntimeError(f"Container {name} not found")
        result = container.exec_run(command, environment=environment)
        output = result.output.decode() if result.output else ""
        return result.exit_code, output

    def copy_from_container(self, name: str, src_path: str, dst_path: Path) -> None:
        container = self._get_container(name)
        if container is None:
            raise RuntimeError(f"Container {name} not found")

        bits, _ = container.get_archive(src_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryFile(dir=dst_path.parent) as tar_stream:
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)

            with tarfile.open(fileobj=tar_stream) as tar:
                members = tar.getmembers()
                # Docker get_archive wraps content under the source basename.
                # Remap paths so the top-level entry becomes dst_path.name.
                src_basename = members[0].name if members else ""
                for member in members:
                    if member.name == src_basename:
                        member.name = dst_path.name
                    else:
                        member.name = str(Path(dst_path.name) / Path(member.name).relative_to(src_basename))
                    tar.extract(member, dst_path.parent, filter="data")

    def copy_to_container(self, name: str, src_path: Path, dst_path: str) -> None:
        container = self._get_container(name)
        if container is None:
            raise RuntimeError(f"Container {name} not found")

        with tempfile.TemporaryFile(dir=src_path.parent) as tar_stream:
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tar.add(str(src_path), arcname=Path(dst_path).name)
            tar_stream.seek(0)

            container.put_archive(str(Path(dst_path).parent), tar_stream)

    def create_container(
        self,
        name: str,
        image: str,
        command: str | list[str],
        volumes: dict[str, dict[str, str]] | None = None,
        user: str = "root",
    ) -> None:
        self._client.containers.create(
            image=image,
            name=name,
            command=command,
            user=user,
            volumes=volumes,
        )

    def start_and_wait(self, name: str) -> tuple[int, str]:
        container = self._get_container(name)
        if container is None:
            raise RuntimeError(f"Container {name} not found")
        container.start()
        result = container.wait()
        logs = container.logs().decode(errors="replace")
        exit_code: int = result.get("StatusCode", 1)
        return exit_code, logs

    def remove_container(self, name: str) -> None:
        container = self._get_container(name)
        if container is not None:
            container.remove(force=True)

    def _get_container(self, name: str) -> Container | None:
        try:
            container: Container = self._client.containers.get(name)
            return container
        except NotFound:
            return None
