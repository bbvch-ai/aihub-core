import io
import logging
import tarfile
import time
from pathlib import Path

import docker
from docker.errors import NotFound
from docker.models.containers import Container

logger = logging.getLogger(__name__)


class DockerManager:
    def __init__(self) -> None:
        self._client = docker.from_env()

    def _get_container(self, name: str) -> Container | None:
        try:
            container: Container = self._client.containers.get(name)
            return container
        except NotFound:
            return None

    def container_exists(self, name: str) -> bool:
        return self._get_container(name) is not None

    def container_is_running(self, name: str) -> bool:
        container = self._get_container(name)
        if container is None:
            return False
        return container.status == "running"

    def stop_container(self, name: str) -> bool:
        container = self._get_container(name)
        if container is None:
            return False
        if container.status != "running":
            return False
        container.stop()
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
        while time.monotonic() < deadline:
            container.reload()
            health = container.attrs.get("State", {}).get("Health")
            if health is None:
                return True  # No healthcheck configured
            status = health.get("Status", "")
            if status == "healthy":
                return True
            time.sleep(5)

        logger.warning("%s did not become healthy within %ds", name, timeout)
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

        tar_stream = io.BytesIO()
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

        tar_stream = io.BytesIO()
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
        logs = container.logs().decode()
        exit_code: int = result.get("StatusCode", 1)
        return exit_code, logs

    def create_and_run_temp_container(
        self,
        name: str,
        image: str,
        command: str | list[str],
        volumes: dict[str, dict[str, str]] | None = None,
        user: str = "root",
    ) -> tuple[int, str]:
        """Uses create + start + wait instead of run because the backup container
        talks to the host Docker daemon via socket and cannot share its filesystem
        with sibling containers.
        """
        try:
            container = self._client.containers.create(
                image=image,
                name=name,
                command=command,
                user=user,
                volumes=volumes,
            )
            container.start()
            result = container.wait()
            logs = container.logs().decode()
            exit_code: int = result.get("StatusCode", 1)
            return exit_code, logs
        finally:
            try:
                temp = self._client.containers.get(name)
                temp.remove(force=True)
            except NotFound:
                pass

    def remove_container(self, name: str) -> None:
        container = self._get_container(name)
        if container is not None:
            container.remove(force=True)
