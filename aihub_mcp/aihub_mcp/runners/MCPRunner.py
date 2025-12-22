"""Standalone runner for the MCP server."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from starlette.applications import Starlette

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


class MCPRunner:
    """
    Complete runner for the MCP server with all services.

    Orchestrates:
    - MCP server setup
    - Agent discovery
    - Event translation
    - Authentication
    - Tracing
    """

    def __init__(self, settings: MCPSettings | None = None) -> None:
        self._settings = settings or MCPSettings()

        # Core components
        self._mcp_server = MCPServer(self._settings)
        self._auth = ApiKeyAuth(self._settings.API_KEY)
        self._tracer = MCPTracer(enabled=self._settings.TRACING_ENABLED)

        # Translation layer
        self._elicitation_handler = ElicitationHandler()
        self._progress_streamer = ProgressStreamer()
        self._sampling_bridge = SamplingBridge()
        self._event_translator = EventTranslator(
            nats_url=self._settings.NATS_URL,
            elicitation_handler=self._elicitation_handler,
            progress_streamer=self._progress_streamer,
            sampling_bridge=self._sampling_bridge,
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

    @asynccontextmanager
    async def lifespan(self, app: Starlette) -> AsyncIterator[None]:
        """Lifecycle manager for all MCP services."""
        logger.info("Starting MCP runner services...")

        # Connect event translator to NATS
        await self._event_translator.connect()

        # Start agent discovery
        await self._discovery_service.start()

        logger.info(f"MCP server ready at http://{self._settings.HOST}:{self._settings.PORT}{self._settings.PATH}")

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
        """Create the complete MCP application."""
        # Initialize MCP server
        self._mcp_server.create_mcp()

        # Create the MCP HTTP/SSE app
        mcp = self._mcp_server.mcp

        if self._settings.TRANSPORT == "sse":
            mcp_app = mcp.sse_app(path="/")
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

        app = Starlette(
            routes=[
                # Mount MCP at configured path
                # Note: Using Starlette Mount requires importing it
            ],
            lifespan=combined_lifespan,
        )

        # Add the MCP app as a mount
        from starlette.routing import Mount

        app.routes.append(Mount(self._settings.PATH, app=mcp_app))

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
