from unittest.mock import MagicMock

import pytest

from aihub_backup.container_lifecycle import (
    ContainerLifecycleManager,
    ServiceDeps,
    _assert_no_overlapping_deps,
)


@pytest.fixture
def docker() -> MagicMock:
    docker = MagicMock()
    docker.container_exists.return_value = True
    docker.stop_container.return_value = True
    docker.wait_for_healthy.return_value = True
    return docker


@pytest.fixture
def lifecycle(docker: MagicMock) -> ContainerLifecycleManager:
    return ContainerLifecycleManager(docker)


def test_stop_containers(lifecycle: ContainerLifecycleManager, docker: MagicMock) -> None:
    lifecycle.stop_containers("test", ("svc-a", "svc-b"))

    assert docker.stop_container.call_count == 2
    stop_names = [call[0][0] for call in docker.stop_container.call_args_list]
    assert "svc-a" in stop_names
    assert "svc-b" in stop_names


def test_start_and_await_healthy(lifecycle: ContainerLifecycleManager, docker: MagicMock) -> None:
    lifecycle.start_and_await_healthy(("svc-a", "svc-b"), timeout=60)

    assert docker.start_container.call_count == 2
    assert docker.wait_for_healthy.call_count == 2


def test_start_and_await_healthy_raises_on_failure(lifecycle: ContainerLifecycleManager, docker: MagicMock) -> None:
    docker.wait_for_healthy.side_effect = lambda name, timeout: name != "svc-b"

    with pytest.raises(RuntimeError, match="failed health check"):
        lifecycle.start_and_await_healthy(("svc-a", "svc-b"), timeout=60)


def test_start_skips_nonexistent_containers(lifecycle: ContainerLifecycleManager, docker: MagicMock) -> None:
    docker.container_exists.return_value = False

    lifecycle.start_and_await_healthy(("missing-svc",), timeout=60)

    docker.start_container.assert_not_called()


def test_assert_no_overlapping_deps_passes_for_disjoint() -> None:
    deps = {
        "A": ServiceDeps(containers=("svc-1", "svc-2"), timeout=60),
        "B": ServiceDeps(containers=("svc-3",), timeout=60),
        "C": ServiceDeps(containers=None, timeout=0),
    }
    _assert_no_overlapping_deps(deps)


def test_assert_no_overlapping_deps_raises_on_overlap() -> None:
    deps = {
        "A": ServiceDeps(containers=("shared",), timeout=60),
        "B": ServiceDeps(containers=("shared",), timeout=60),
    }
    with pytest.raises(AssertionError, match="Container 'shared' claimed by both 'A' and 'B'"):
        _assert_no_overlapping_deps(deps)
