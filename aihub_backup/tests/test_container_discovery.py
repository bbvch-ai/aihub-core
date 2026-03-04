from unittest.mock import MagicMock, patch

import pytest

from aihub_backup.container_discovery import ContainerDiscovery


def _mock_container(name: str, status: str = "running", project: str = "aihub") -> MagicMock:
    c = MagicMock()
    c.name = name
    c.status = status
    c.labels = {"com.docker.compose.project": project}
    return c


@pytest.fixture
def discovery() -> ContainerDiscovery:
    with (
        patch("aihub_backup.container_discovery.docker") as mock_docker,
        patch("aihub_backup.container_discovery.socket") as mock_socket,
    ):
        mock_socket.gethostname.return_value = "backup-code-1"
        client = MagicMock()
        mock_docker.from_env.return_value = client

        self_container = MagicMock()
        self_container.labels = {"com.docker.compose.project": "aihub"}
        client.containers.get.return_value = self_container

        cd = ContainerDiscovery()
        assert cd._project == "aihub"
        return cd


def test_discover_managed_containers(discovery: ContainerDiscovery) -> None:
    discovery._client.containers.list.return_value = [
        _mock_container("api"),
        _mock_container("web"),
        _mock_container("seaweedfs-master"),
        _mock_container("etcd"),
        _mock_container("backup-code"),
    ]

    managed = discovery.discover_managed_containers()

    assert "api" in managed
    assert "web" in managed
    assert "seaweedfs-master" not in managed
    assert "etcd" not in managed
    assert "backup-code" not in managed


def test_stop_all_managed_returns_previously_running(discovery: ContainerDiscovery) -> None:
    running = _mock_container("api", status="running")
    stopped = _mock_container("web", status="exited")
    excluded = _mock_container("seaweedfs-master", status="running")

    discovery._client.containers.list.return_value = [running, stopped, excluded]

    previously_running = discovery.stop_all_managed()

    assert previously_running == ["api"]
    running.stop.assert_called_once_with(timeout=30)
    stopped.stop.assert_not_called()
    excluded.stop.assert_not_called()


def test_start_all_starts_stopped_containers(discovery: ContainerDiscovery) -> None:
    container = MagicMock()
    container.status = "exited"
    discovery._client.containers.get.return_value = container

    discovery.start_all(["api", "web"])

    assert container.start.call_count == 2


def test_start_all_skips_running_containers(discovery: ContainerDiscovery) -> None:
    container = MagicMock()
    container.status = "running"
    discovery._client.containers.get.return_value = container

    discovery.start_all(["api"])

    container.start.assert_not_called()


def test_start_all_handles_missing_container(discovery: ContainerDiscovery) -> None:
    from docker.errors import NotFound

    discovery._client.containers.get.side_effect = NotFound("gone")

    discovery.start_all(["gone-container"])


def test_detect_project_raises_without_label() -> None:
    with (
        patch("aihub_backup.container_discovery.docker") as mock_docker,
        patch("aihub_backup.container_discovery.socket") as mock_socket,
    ):
        mock_socket.gethostname.return_value = "backup-code-1"
        client = MagicMock()
        mock_docker.from_env.return_value = client

        self_container = MagicMock()
        self_container.labels = {}
        client.containers.get.return_value = self_container

        with pytest.raises(RuntimeError, match="no.*label"):
            ContainerDiscovery()


def test_detect_project_raises_when_container_not_found() -> None:
    from docker.errors import NotFound

    with (
        patch("aihub_backup.container_discovery.docker") as mock_docker,
        patch("aihub_backup.container_discovery.socket") as mock_socket,
    ):
        mock_socket.gethostname.return_value = "backup-code-1"
        client = MagicMock()
        mock_docker.from_env.return_value = client
        client.containers.get.side_effect = NotFound("not found")

        with pytest.raises(RuntimeError, match="Docker socket"):
            ContainerDiscovery()


def test_is_excluded() -> None:
    assert ContainerDiscovery._is_excluded("backup-code") is True
    assert ContainerDiscovery._is_excluded("backup-daemon") is True
    assert ContainerDiscovery._is_excluded("seaweedfs-master") is True
    assert ContainerDiscovery._is_excluded("etcd") is True
    assert ContainerDiscovery._is_excluded("api") is False
    assert ContainerDiscovery._is_excluded("postgres") is False
