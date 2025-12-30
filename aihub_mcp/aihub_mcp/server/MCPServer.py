import logging
from typing import Any

from fastmcp import FastMCP

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

    Note: Use MCPRunner.create_app() to create the full application with
    authentication and tracing middleware.
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
