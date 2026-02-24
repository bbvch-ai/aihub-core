from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.docker_client import DockerManager


@pytest.fixture
def docker_manager() -> DockerManager:
    with patch("aihub_backup.docker_client.docker.from_env") as mock_from_env:
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        manager = DockerManager()
        return manager


def test_exec_in_container_passes_environment(docker_manager: DockerManager) -> None:
    """exec_in_container forwards the environment dict to container.exec_run."""
    container = MagicMock()
    container.exec_run.return_value = MagicMock(exit_code=0, output=b"OK")
    docker_manager._client.containers.get.return_value = container

    env = {"MY_VAR": "my_value"}
    exit_code, output = docker_manager.exec_in_container("test-container", ["echo", "hello"], environment=env)

    container.exec_run.assert_called_once_with(["echo", "hello"], environment=env)
    assert exit_code == 0


def test_exec_in_container_without_environment(docker_manager: DockerManager) -> None:
    """exec_in_container works without environment parameter."""
    container = MagicMock()
    container.exec_run.return_value = MagicMock(exit_code=0, output=b"OK")
    docker_manager._client.containers.get.return_value = container

    docker_manager.exec_in_container("test-container", ["echo", "hello"])

    container.exec_run.assert_called_once_with(["echo", "hello"], environment=None)


def test_exec_in_container_raises_when_not_found(docker_manager: DockerManager) -> None:
    """exec_in_container raises RuntimeError when container not found."""
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")

    with pytest.raises(RuntimeError, match="not found"):
        docker_manager.exec_in_container("missing", ["echo"])


def test_copy_from_container_uses_filter_data(docker_manager: DockerManager, tmp_path: Path) -> None:
    """copy_from_container extracts tar with filter='data' for path traversal safety."""
    import io
    import tarfile

    container = MagicMock()
    docker_manager._client.containers.get.return_value = container

    # Create a tar archive in memory
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        info = tarfile.TarInfo(name="test.txt")
        data = b"hello world"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tar_stream.seek(0)

    container.get_archive.return_value = ([tar_stream.read()], None)

    dst = tmp_path / "test.txt"

    with patch("tarfile.TarFile.extract") as mock_extract:
        docker_manager.copy_from_container("test-container", "/src/test.txt", dst)

        assert mock_extract.called
        for call in mock_extract.call_args_list:
            assert call.kwargs.get("filter") == "data"


def test_create_and_run_temp_container_cleans_up(docker_manager: DockerManager) -> None:
    """Temp container is removed after execution."""
    container = MagicMock()
    container.wait.return_value = {"StatusCode": 0}
    container.logs.return_value = b"output"
    docker_manager._client.containers.create.return_value = container
    docker_manager._client.containers.get.return_value = container

    exit_code, logs = docker_manager.create_and_run_temp_container(
        name="temp-test",
        image="test:latest",
        command=["echo", "hello"],
    )

    assert exit_code == 0
    assert logs == "output"
    container.remove.assert_called_once_with(force=True)


def test_create_and_run_temp_container_cleans_up_on_failure(docker_manager: DockerManager) -> None:
    """Temp container is removed even when execution fails."""
    container = MagicMock()
    container.start.side_effect = RuntimeError("start failed")
    docker_manager._client.containers.create.return_value = container
    docker_manager._client.containers.get.return_value = container

    with pytest.raises(RuntimeError, match="start failed"):
        docker_manager.create_and_run_temp_container(
            name="temp-test",
            image="test:latest",
            command=["echo", "hello"],
        )

    container.remove.assert_called_once_with(force=True)


def test_wait_for_healthy_timeout(docker_manager: DockerManager) -> None:
    """wait_for_healthy returns False when container doesn't become healthy."""
    container = MagicMock()
    container.attrs = {"State": {"Health": {"Status": "starting"}}}
    docker_manager._client.containers.get.return_value = container

    with patch("aihub_backup.docker_client.time.sleep"):
        result = docker_manager.wait_for_healthy("test-container", timeout=5)

    assert result is False


def test_wait_for_healthy_succeeds(docker_manager: DockerManager) -> None:
    """wait_for_healthy returns True when container becomes healthy."""
    container = MagicMock()
    container.attrs = {"State": {"Health": {"Status": "healthy"}}}
    docker_manager._client.containers.get.return_value = container

    result = docker_manager.wait_for_healthy("test-container", timeout=30)

    assert result is True


# ---------------------------------------------------------------------------
# container_exists / container_is_running
# ---------------------------------------------------------------------------


def test_container_exists_true(docker_manager: DockerManager) -> None:
    docker_manager._client.containers.get.return_value = MagicMock()
    assert docker_manager.container_exists("my-container") is True


def test_container_exists_false(docker_manager: DockerManager) -> None:
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")
    assert docker_manager.container_exists("missing") is False


def test_container_is_running_true(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.status = "running"
    docker_manager._client.containers.get.return_value = container
    assert docker_manager.container_is_running("my-container") is True


def test_container_is_running_false_when_stopped(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.status = "exited"
    docker_manager._client.containers.get.return_value = container
    assert docker_manager.container_is_running("my-container") is False


def test_container_is_running_false_when_missing(docker_manager: DockerManager) -> None:
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")
    assert docker_manager.container_is_running("missing") is False


# ---------------------------------------------------------------------------
# stop_container / start_container
# ---------------------------------------------------------------------------


def test_stop_container_running(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.status = "running"
    docker_manager._client.containers.get.return_value = container

    assert docker_manager.stop_container("my-container") is True
    container.stop.assert_called_once()


def test_stop_container_already_stopped(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.status = "exited"
    docker_manager._client.containers.get.return_value = container

    assert docker_manager.stop_container("my-container") is False
    container.stop.assert_not_called()


def test_stop_container_not_found(docker_manager: DockerManager) -> None:
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")
    assert docker_manager.stop_container("missing") is False


def test_start_container(docker_manager: DockerManager) -> None:
    container = MagicMock()
    docker_manager._client.containers.get.return_value = container

    assert docker_manager.start_container("my-container") is True
    container.start.assert_called_once()


def test_start_container_not_found(docker_manager: DockerManager) -> None:
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")
    assert docker_manager.start_container("missing") is False


# ---------------------------------------------------------------------------
# get_container_image / get_volume_mount
# ---------------------------------------------------------------------------


def test_get_container_image(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.image.tags = ["neo4j:5.26-community"]
    docker_manager._client.containers.get.return_value = container

    assert docker_manager.get_container_image("neo4j") == "neo4j:5.26-community"


def test_get_container_image_no_tags_falls_back_to_id(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.image.tags = []
    container.image.id = "sha256:abc123"
    docker_manager._client.containers.get.return_value = container

    assert docker_manager.get_container_image("neo4j") == "sha256:abc123"


def test_get_container_image_not_found(docker_manager: DockerManager) -> None:
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")
    assert docker_manager.get_container_image("missing") is None


def test_get_volume_mount(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.attrs = {"Mounts": [{"Destination": "/data", "Source": "/vol/neo4j/data"}]}
    docker_manager._client.containers.get.return_value = container

    assert docker_manager.get_volume_mount("neo4j", "/data") == "/vol/neo4j/data"


def test_get_volume_mount_not_found(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.attrs = {"Mounts": [{"Destination": "/data", "Source": "/vol/data"}]}
    docker_manager._client.containers.get.return_value = container

    assert docker_manager.get_volume_mount("neo4j", "/logs") is None


# ---------------------------------------------------------------------------
# copy_to_container / create_container / start_and_wait / remove_container
# ---------------------------------------------------------------------------


def test_copy_to_container(docker_manager: DockerManager, tmp_path: Path) -> None:
    container = MagicMock()
    docker_manager._client.containers.get.return_value = container

    src = tmp_path / "dump.sql"
    src.write_text("data")

    docker_manager.copy_to_container("my-container", src, "/tmp/dump.sql")

    container.put_archive.assert_called_once()
    call_args = container.put_archive.call_args
    assert call_args[0][0] == "/tmp"


def test_create_container(docker_manager: DockerManager) -> None:
    docker_manager.create_container(
        name="test-container",
        image="test:latest",
        command=["echo", "hello"],
        volumes={"/host/path": {"bind": "/data", "mode": "rw"}},
    )

    docker_manager._client.containers.create.assert_called_once_with(
        image="test:latest",
        name="test-container",
        command=["echo", "hello"],
        user="root",
        volumes={"/host/path": {"bind": "/data", "mode": "rw"}},
    )


def test_start_and_wait(docker_manager: DockerManager) -> None:
    container = MagicMock()
    container.wait.return_value = {"StatusCode": 0}
    container.logs.return_value = b"success"
    docker_manager._client.containers.get.return_value = container

    exit_code, logs = docker_manager.start_and_wait("my-container")

    assert exit_code == 0
    assert logs == "success"
    container.start.assert_called_once()


def test_start_and_wait_not_found(docker_manager: DockerManager) -> None:
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")

    with pytest.raises(RuntimeError, match="not found"):
        docker_manager.start_and_wait("missing")


def test_remove_container(docker_manager: DockerManager) -> None:
    container = MagicMock()
    docker_manager._client.containers.get.return_value = container

    docker_manager.remove_container("my-container")

    container.remove.assert_called_once_with(force=True)


def test_remove_container_not_found_is_noop(docker_manager: DockerManager) -> None:
    from docker.errors import NotFound

    docker_manager._client.containers.get.side_effect = NotFound("not found")

    docker_manager.remove_container("missing")  # Should not raise
