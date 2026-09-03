import socket
import time

import pytest
from pydantic import BaseModel

from swiss_ai_hub.core.routes.health.health_server import HealthCheckProvider, HealthServer


class _FakeChecks(BaseModel):
    running: bool = True


class _FakeProvider(HealthCheckProvider):
    @property
    def entity_name(self) -> str:
        return "FakeEntity"

    @property
    def entity_type(self) -> str:
        return "agent"

    def get_readiness_checks(self) -> BaseModel:
        return _FakeChecks()


def _free_port() -> int:
    """Ask the OS for a currently-unused ephemeral port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]


def _wait_until(predicate, timeout: float = 5.0, interval: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


@pytest.mark.unit
def test_binds_the_requested_port() -> None:
    """The server must bind exactly the configured port -- never a random fallback."""
    port = _free_port()
    server = HealthServer(_FakeProvider(), default_port=port, bind_retry_seconds=0.05)

    server.start()
    try:
        assert _wait_until(lambda: server.port == port)

        with socket.create_connection(("127.0.0.1", port), timeout=2) as sock:
            sock.sendall(b"GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
            response = sock.recv(4096)
        assert b"200" in response
    finally:
        server.stop()


@pytest.mark.unit
def test_retries_and_eventually_binds_when_port_initially_occupied() -> None:
    """If the port is briefly held by another socket, the server retries until it succeeds.

    Regression guard: a pre-bind availability check used to report the port as permanently
    occupied (e.g. TIME_WAIT sockets without SO_REUSEADDR) and silently fall back to a random
    port. The fix removes the pre-check entirely and retries the real bind instead.
    """
    port = _free_port()
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("0.0.0.0", port))
    blocker.listen(1)

    server = HealthServer(_FakeProvider(), default_port=port, bind_retry_seconds=0.05)
    server.start()
    try:
        # Give the server a couple of retry cycles to observe the occupied port.
        time.sleep(0.2)
        assert server.port is None

        blocker.close()

        assert _wait_until(lambda: server.port == port)
    finally:
        server.stop()


@pytest.mark.unit
def test_stop_is_safe_when_never_bound() -> None:
    """stop() must not hang or raise if the port never became available."""
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("0.0.0.0", 0))
    port = blocker.getsockname()[1]
    blocker.listen(1)

    server = HealthServer(_FakeProvider(), default_port=port, bind_retry_seconds=0.05)
    server.start()
    try:
        time.sleep(0.15)
        assert server.port is None
    finally:
        server.stop()
        blocker.close()

    assert server.port is None


@pytest.mark.unit
def test_resolves_port_from_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    port = _free_port()
    monkeypatch.setenv("MY_HEALTH_PORT", str(port))
    server = HealthServer(_FakeProvider(), default_port=9999, port_env_var="MY_HEALTH_PORT")

    assert server._resolve_port() == port
