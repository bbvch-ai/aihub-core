"""Prove the pooled client actually reuses TCP connections, not merely that it is the same object.

The sibling tests assert client identity, which is as far as they can go — identity says nothing about
whether the connection pool underneath survives between requests. This drives a real socket against a
local `http.server` and counts accepted connections, which is the property the pooling exists for, and
the only one here that fails against the pre-pooling code.

Marked `unit`, not `integration`: it binds a loopback port on an OS-assigned number but reaches no
external service, so it stays hermetic and runs in well under a second. `integration` in this repo means
"needs the docker stack", and that marker would keep the only check of the pooling AC out of `make test`.
"""

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

pytestmark = pytest.mark.unit

_REQUEST_COUNT = 10


class _KeepAliveHandler(BaseHTTPRequestHandler):
    """HTTP/1.1 with an explicit Content-Length, so the server holds the connection open between requests."""

    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        body = b'{"status": "ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: Any) -> None:
        pass


class _ConnectionCountingServer(ThreadingHTTPServer):
    """Threaded so a second connection is accepted and counted rather than left queued behind the first."""

    daemon_threads = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.accepted_connections = 0

    def get_request(self) -> Any:
        self.accepted_connections += 1
        return super().get_request()


@contextmanager
def _running_server() -> Iterator[_ConnectionCountingServer]:
    server = _ConnectionCountingServer(("127.0.0.1", 0), _KeepAliveHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.asyncio
async def test_sequential_requests_open_exactly_one_tcp_connection() -> None:
    with _running_server() as server:
        settings = LiteLLMProxySettings(BASE_URL=f"http://127.0.0.1:{server.server_port}", API_KEY="sk-master")

        for _ in range(_REQUEST_COUNT):
            response = await settings.httpx_aclient.get("/health")
            assert response.status_code == 200

        await LiteLLMProxySettings.aclose_pooled_clients()

        assert server.accepted_connections == 1
