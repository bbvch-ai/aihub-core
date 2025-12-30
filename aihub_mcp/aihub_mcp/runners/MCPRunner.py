import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount

from aihub_mcp.auth.ApiKeyAuth import ApiKeyAuth
from aihub_mcp.discovery.AgentDiscoveryService import AgentDiscoveryService
from aihub_mcp.discovery.PromptRegistry import PromptRegistry
from aihub_mcp.server.AgentToolRegistry import AgentToolRegistry
from aihub_mcp.server.MCPServer import MCPServer
from aihub_mcp.server.ResourceRegistry import ResourceRegistry
from aihub_mcp.settings.MCPSettings import MCPSettings
from aihub_mcp.tracing.MCPTracer import MCPTracer
from aihub_mcp.translation.ElicitationHandler import ElicitationHandler
from aihub_mcp.translation.EventTranslator import EventTranslator
from aihub_mcp.translation.ProgressStreamer import ProgressStreamer
from aihub_mcp.translation.SamplingBridge import SamplingBridge

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key authentication on MCP requests."""

    def __init__(self, app: Any, auth: ApiKeyAuth, tracer: MCPTracer) -> None:
        super().__init__(app)
        self._auth = auth
        self._tracer = tracer

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        # Start tracing span for the request
        span = self._tracer.start_tool_span(
            tool_name="mcp_request",
            agent_class="mcp_server",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
            },
        )

        try:
            # Skip auth for health checks and OPTIONS
            if request.method == "OPTIONS" or request.url.path.endswith("/health"):
                response = await call_next(request)
                self._tracer.end_span(span, success=True)
                return response

            # Validate API key if auth is enabled
            if self._auth.enabled:
                headers = dict(request.headers)
                if not self._auth.validate(headers):
                    self._tracer.end_span(span, success=False, error_message="Unauthorized")
                    return JSONResponse(
                        status_code=401,
                        content={"error": "Unauthorized", "message": "Invalid or missing API key"},
                    )

                # Store user identity in request state
                request.state.user = self._auth.get_user_identity(headers)

            response = await call_next(request)
            self._tracer.end_span(span, success=True)
            return response

        except Exception as e:
            self._tracer.end_span(span, success=False, error_message=str(e))
            raise


class MCPRunner:
    """
    Complete runner for the MCP server with all services.

    Orchestrates:
    - MCP server setup
    - Agent discovery
    - Event translation
    - Authentication (wired via middleware)
    - Tracing (wired via middleware)
    """

    def __init__(self, settings: MCPSettings | None = None) -> None:
        self._settings = settings or MCPSettings()

        # Core components
        self._mcp_server = MCPServer(self._settings)
        self._auth = ApiKeyAuth(
            api_keys=self._settings.get_all_api_keys(),
            rate_limit_per_minute=self._settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        )
        self._tracer = MCPTracer(
            service_name="aihub_mcp",
            enabled=self._settings.TRACING_ENABLED,
        )

        # Translation layer
        self._elicitation_handler = ElicitationHandler()
        self._progress_streamer = ProgressStreamer(
            mask_sensitive_data=self._settings.MASK_SENSITIVE_DATA,
        )
        self._sampling_bridge = SamplingBridge()
        self._event_translator = EventTranslator(
            nats_url=self._settings.NATS_URL,
            elicitation_handler=self._elicitation_handler,
            progress_streamer=self._progress_streamer,
            sampling_bridge=self._sampling_bridge,
            tracer=self._tracer,
            agent_timeout_seconds=self._settings.AGENT_TIMEOUT_SECONDS,
            mask_sensitive_data=self._settings.MASK_SENSITIVE_DATA,
        )

        # Registries
        self._tool_registry = AgentToolRegistry(
            mcp_server=self._mcp_server,
            event_translator=self._event_translator,
        )
        self._resource_registry = ResourceRegistry(self._mcp_server)
        self._prompt_registry = PromptRegistry(self._mcp_server)

        # Discovery
        self._discovery_service = AgentDiscoveryService(
            settings=self._settings,
            mcp_server=self._mcp_server,
            tool_registry=self._tool_registry,
            resource_registry=self._resource_registry,
        )

    @property
    def settings(self) -> MCPSettings:
        return self._settings

    @property
    def mcp_server(self) -> MCPServer:
        return self._mcp_server

    @property
    def auth(self) -> ApiKeyAuth:
        return self._auth

    @property
    def tracer(self) -> MCPTracer:
        return self._tracer

    @asynccontextmanager
    async def lifespan(self, app: Starlette) -> AsyncIterator[None]:
        """Lifecycle manager for all MCP services."""
        logger.info("Starting MCP runner services...")

        # Connect event translator to NATS
        await self._event_translator.connect()

        # Start agent discovery
        await self._discovery_service.start()

        auth_status = "enabled" if self._auth.enabled else "disabled"
        tracing_status = "enabled" if self._settings.TRACING_ENABLED else "disabled"
        logger.info(
            f"MCP server ready at http://{self._settings.HOST}:{self._settings.PORT}{self._settings.PATH} "
            f"(auth={auth_status}, tracing={tracing_status})"
        )

        try:
            yield
        finally:
            logger.info("Stopping MCP runner services...")

            # Stop discovery
            await self._discovery_service.stop()

            # Disconnect event translator
            await self._event_translator.disconnect()

            logger.info("MCP runner services stopped")

    def create_app(self) -> Starlette:
        """Create the complete MCP application with auth and tracing middleware."""
        # Initialize MCP server
        self._mcp_server.create_mcp()

        # Create the MCP HTTP/SSE app
        mcp = self._mcp_server.mcp

        if self._settings.TRANSPORT == "sse":
            mcp_app = mcp.sse_app(path="/")  # type: ignore[attr-defined]
            logger.info("Using SSE transport")
        else:
            mcp_app = mcp.http_app(path="/")
            logger.info("Using Streamable HTTP transport")

        @asynccontextmanager
        async def combined_lifespan(app: Starlette) -> AsyncIterator[None]:
            # Critical: MCP lifespan must initialize FIRST for session management
            async with mcp_app.lifespan(mcp_app):
                async with self.lifespan(app):
                    yield

        # Create app with auth middleware
        app = Starlette(
            routes=[Mount(self._settings.PATH, app=mcp_app)],
            lifespan=combined_lifespan,
            middleware=[
                Middleware(AuthMiddleware, auth=self._auth, tracer=self._tracer),
            ],
        )

        return app

    def run(self) -> None:
        """Run the MCP server using uvicorn."""
        import uvicorn

        # Configure logging
        log_level = "debug" if self._settings.DEBUG else "info"
        logging.basicConfig(level=log_level.upper())

        app = self.create_app()

        logger.info(f"Starting MCP server on {self._settings.HOST}:{self._settings.PORT}")

        uvicorn.run(
            app,
            host=self._settings.HOST,
            port=self._settings.PORT,
            log_level=log_level,
        )
