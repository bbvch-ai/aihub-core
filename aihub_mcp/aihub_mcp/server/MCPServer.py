"""Main MCP server implementation using FastMCP."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount

from aihub_mcp.settings.MCPSettings import MCPSettings

logger = logging.getLogger(__name__)


class MCPServer:
    """
    Full-featured MCP server bridging Swiss AI Agent Protocol with Model Context Protocol.

    This server exposes AI Hub agents as MCP tools, enabling external clients like Claude Code,
    Cursor, and VS Code extensions to interact with agents using the MCP specification.

    Key capabilities:
    - Dynamic agent discovery and tool registration
    - Human-in-the-loop via MCP elicitation
    - LLM sampling from MCP client
    - Progress streaming for agent thoughts and outputs
    """

    def __init__(self, settings: MCPSettings | None = None) -> None:
        self._settings = settings or MCPSettings()
        self._mcp: FastMCP | None = None
        self._agent_registry: dict[str, dict[str, Any]] = {}

    @property
    def settings(self) -> MCPSettings:
        return self._settings

    @property
    def mcp(self) -> FastMCP:
        if self._mcp is None:
            raise RuntimeError("MCP server not initialized. Call create_mcp() first.")
        return self._mcp

    def create_mcp(self) -> FastMCP:
        """Create and configure the FastMCP instance."""
        self._mcp = FastMCP(
            name="Swiss AI Hub Agents",
            instructions=(
                "This MCP server provides access to Swiss AI Hub agents. "
                "Each agent is exposed as a tool that you can invoke to perform specific tasks. "
                "Agents support human-in-the-loop workflows via elicitation and can stream "
                "progress updates during execution."
            ),
        )

        # Register static resources
        self._register_resources()

        # Register static prompts
        self._register_prompts()

        logger.info("FastMCP instance created: Swiss AI Hub Agents")
        return self._mcp

    def _register_resources(self) -> None:
        """Register static MCP resources for agent metadata."""

        @self.mcp.resource("agents://list")
        async def list_agents() -> dict[str, Any]:
            """List all available agents with their metadata."""
            return {
                "agents": list(self._agent_registry.values()),
                "count": len(self._agent_registry),
            }

        @self.mcp.resource("agents://{agent_class}")
        async def get_agent(agent_class: str) -> dict[str, Any]:
            """Get metadata for a specific agent class."""
            if agent_class not in self._agent_registry:
                return {"error": f"Agent '{agent_class}' not found"}
            return self._agent_registry[agent_class]

        logger.debug("MCP resources registered")

    def _register_prompts(self) -> None:
        """Register static MCP prompts for common operations."""
        from fastmcp.prompts.prompt import PromptMessage, TextContent  # type: ignore[attr-defined]

        @self.mcp.prompt
        def analyze_with_agent(agent_name: str, query: str) -> PromptMessage:
            """Create a prompt to analyze something using a specific agent."""
            text = f"Use the {agent_name} agent to analyze the following:\n\n{query}"
            return PromptMessage(role="user", content=TextContent(type="text", text=text))

        @self.mcp.prompt
        def list_available_agents() -> PromptMessage:
            """Create a prompt to list all available agents."""
            text = "Please list all available AI Hub agents and their capabilities."
            return PromptMessage(role="user", content=TextContent(type="text", text=text))

        logger.debug("MCP prompts registered")

    def register_agent(
        self,
        agent_class: str,
        is_conversational: bool,
        start_events: list[dict[str, Any]],
        stop_events: list[dict[str, Any]],
        hitl_request_events: list[dict[str, Any]],
        hitl_response_events: list[dict[str, Any]],
        agent_config_specs: dict[str, Any],
        default_agent_config: dict[str, Any],
    ) -> None:
        """
        Register an agent discovered via SAAP as an MCP tool.

        This method is called by AgentDiscoveryService when agents are discovered.
        Each agent's start events become MCP tools.
        """
        self._agent_registry[agent_class] = {
            "agent_class": agent_class,
            "is_conversational": is_conversational,
            "start_events": start_events,
            "stop_events": stop_events,
            "hitl_request_events": hitl_request_events,
            "hitl_response_events": hitl_response_events,
            "agent_config_specs": agent_config_specs,
            "default_agent_config": default_agent_config,
        }
        logger.info(f"Agent registered: {agent_class}")

    def unregister_agent(self, agent_class: str) -> None:
        """Remove an agent from the registry (when it goes offline)."""
        if agent_class in self._agent_registry:
            del self._agent_registry[agent_class]
            logger.info(f"Agent unregistered: {agent_class}")

    @asynccontextmanager
    async def lifespan(self, app: Starlette) -> AsyncIterator[None]:
        """Lifecycle manager for the MCP server."""
        logger.info("MCP server starting up...")

        # Initialize connections (NATS, etc.) will be done by discovery service
        yield

        logger.info("MCP server shutting down...")

    def create_app(self) -> Starlette:
        """
        Create the Starlette application with MCP mounted.

        Returns a Starlette app that can be run with uvicorn or mounted in another app.
        """
        if self._mcp is None:
            self.create_mcp()

        # Create the MCP HTTP app based on transport setting
        if self._settings.TRANSPORT == "sse":
            mcp_app = self.mcp.sse_app(path="/")  # type: ignore[attr-defined]
            logger.info("Using SSE transport (legacy)")
        else:
            mcp_app = self.mcp.http_app(path="/")
            logger.info("Using Streamable HTTP transport (recommended)")

        @asynccontextmanager
        async def combined_lifespan(app: Starlette) -> AsyncIterator[None]:
            # Critical: MCP lifespan must initialize FIRST for session management
            async with mcp_app.lifespan(mcp_app):
                async with self.lifespan(app):
                    yield

        app = Starlette(
            routes=[Mount(self._settings.PATH, app=mcp_app)],
            lifespan=combined_lifespan,
        )

        logger.info(f"MCP app created at path: {self._settings.PATH}")
        return app

    def run(self) -> None:
        """Run the MCP server standalone using uvicorn."""
        import uvicorn

        app = self.create_app()
        uvicorn.run(
            app,
            host=self._settings.HOST,
            port=self._settings.PORT,
            log_level="debug" if self._settings.DEBUG else "info",
        )
