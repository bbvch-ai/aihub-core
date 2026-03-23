import json
import logging
import os
import socket
import threading
from abc import ABC, abstractmethod
from http.server import BaseHTTPRequestHandler, HTTPServer

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HealthCheckProvider(ABC):
    """
    Interface for providing health check information.

    Runners (AgentRunner, ProcessRunner) implement this to provide
    their specific health check logic.
    """

    @property
    @abstractmethod
    def entity_name(self) -> str:
        """The name of the entity (e.g., agent_class or process_class)."""
        ...

    @property
    @abstractmethod
    def entity_type(self) -> str:
        """The type of entity ('agent' or 'process')."""
        ...

    @abstractmethod
    def get_readiness_checks(self) -> BaseModel:
        """
        Returns a Pydantic model containing all readiness check results.

        The model should have boolean fields for each check (e.g., running, nats, redis).
        """
        ...

    def is_ready(self, checks: BaseModel) -> bool:
        """
        Determines if the service is ready based on the checks.

        By default, all boolean fields must be True for the service to be ready.
        Override this method for custom logic.
        """
        for field_name, field_value in checks:
            if isinstance(field_value, bool) and not field_value:
                return False
        return True


class HealthServer:
    """
    HTTP server for health check endpoints.

    Runs in a background thread and exposes:
    - /health: Simple liveness check
    - /health/ready: Readiness check with dependency status
    """

    def __init__(
        self,
        provider: HealthCheckProvider,
        default_port: int = 8090,
        port_env_var: str | None = None,
    ):
        """
        Initialize the health server.
        """
        self.provider = provider
        self.default_port = default_port
        self.port_env_var = port_env_var

        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._port: int | None = None

    @property
    def port(self) -> int | None:
        """The port the server is running on, or None if not started."""
        return self._port

    def _create_handler(self) -> type[BaseHTTPRequestHandler]:
        """Creates an HTTP request handler with access to the provider."""
        provider = self.provider

        class HealthHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                # Suppress default logging to avoid cluttering logs
                pass

            def do_GET(self) -> None:
                if self.path == "/health":
                    self._handle_liveness()
                elif self.path == "/health/ready":
                    self._handle_readiness()
                else:
                    self.send_error(404, "Not Found")

            def _handle_liveness(self) -> None:
                """Simple liveness check - confirms the process is running."""
                health_status = {
                    "status": "ok",
                    f"{provider.entity_type}_class": provider.entity_name,
                }
                self._send_json_response(200, health_status)

            def _handle_readiness(self) -> None:
                """Readiness check - verifies all dependencies are available."""
                checks = provider.get_readiness_checks()
                is_healthy = provider.is_ready(checks)

                health_status = {
                    "status": "ok" if is_healthy else "unhealthy",
                    f"{provider.entity_type}_class": provider.entity_name,
                    "checks": checks.model_dump(),
                }

                status_code = 200 if is_healthy else 503
                self._send_json_response(status_code, health_status)

            def _send_json_response(self, status_code: int, data: dict) -> None:
                response_body = json.dumps(data).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)

        return HealthHandler

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for binding."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return True
            except OSError:
                return False

    def _find_free_port(self) -> int:
        """Find a random available port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 0))
            return s.getsockname()[1]

    def _resolve_port(self) -> int:
        """Determine which port to use based on env var, default, or fallback."""
        if self.port_env_var:
            env_port = os.environ.get(self.port_env_var)
            if env_port is not None:
                port = int(env_port)
                if not self._is_port_available(port):
                    raise OSError(f"{self.port_env_var}={port} is not available. Port is already in use.")
                return port

        if self._is_port_available(self.default_port):
            return self.default_port

        port = self._find_free_port()
        logger.warning(f"Default health port {self.default_port} is occupied, falling back to port {port}")
        return port

    def start(self) -> None:
        """Start the HTTP health check server in a background thread."""
        if self._server is not None:
            logger.warning("Health server is already running")
            return

        self._port = self._resolve_port()
        handler_class = self._create_handler()
        self._server = HTTPServer(("0.0.0.0", self._port), handler_class)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Health check server started on port {self._port}")

    def stop(self) -> None:
        """Stop the HTTP health check server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self._port = None
        logger.debug("Health check server stopped")
