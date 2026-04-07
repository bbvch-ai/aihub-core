from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.backup.container_lifecycle import SERVICE_DEPS, ContainerLifecycleManager
from swiss_ai_hub.backup.models import BACKUP_SERVICES


def test_service_deps_matches_backup_services() -> None:
    assert set(SERVICE_DEPS.keys()) == set(BACKUP_SERVICES)


def test_start_and_await_healthy_succeeds() -> None:
    docker = MagicMock()
    docker.container_exists.return_value = True
    docker.wait_for_healthy.return_value = True

    manager = ContainerLifecycleManager(docker)
    manager.start_and_await_healthy(("postgres", "postgres-ferretdb"), timeout=60, label="PostgreSQL")

    assert docker.start_container.call_count == 2
    assert docker.wait_for_healthy.call_count == 2


def test_start_and_await_healthy_raises_on_failure() -> None:
    docker = MagicMock()
    docker.container_exists.return_value = True
    docker.wait_for_healthy.return_value = False

    manager = ContainerLifecycleManager(docker)

    with pytest.raises(RuntimeError, match="Containers failed health check"):
        manager.start_and_await_healthy(("postgres",), timeout=60)


def test_start_and_await_healthy_skips_missing_containers() -> None:
    docker = MagicMock()
    docker.container_exists.side_effect = lambda name: name == "postgres"
    docker.wait_for_healthy.return_value = True

    manager = ContainerLifecycleManager(docker)
    manager.start_and_await_healthy(("postgres", "missing-container"), timeout=60)

    docker.start_container.assert_called_once_with("postgres")


def test_stop_containers() -> None:
    docker = MagicMock()
    docker.stop_container.return_value = True

    manager = ContainerLifecycleManager(docker)
    manager.stop_containers("PostgreSQL", ("postgres", "postgres-ferretdb"))

    assert docker.stop_container.call_count == 2
