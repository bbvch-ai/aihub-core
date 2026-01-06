import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from aihub_mcp.settings.MCPSettings import MCPSettings

logger = logging.getLogger(__name__)


class EventSpec(BaseModel):
    """Schema for an event specification from agent discovery."""

    event_name: Annotated[str, Field(description="Name of the event")]
    event_schema: Annotated[dict[str, Any], Field(description="JSON schema for event parameters")]
    event_parents: Annotated[list[str], Field(default_factory=list, description="Parent event names")]


class AgentMetadata(BaseModel):
    """Metadata for a registered agent."""

    agent_class: Annotated[str, Field(description="Agent class name")]
    is_conversational: Annotated[bool, Field(description="Whether agent supports conversation")]
    start_events: Annotated[list[EventSpec], Field(description="Events that can start the agent")]
    stop_events: Annotated[list[EventSpec], Field(description="Events that stop the agent")]
    hitl_request_events: Annotated[list[EventSpec], Field(description="HITL request event specs")]
    hitl_response_events: Annotated[list[EventSpec], Field(description="HITL response event specs")]
    agent_config_specs: Annotated[dict[str, Any], Field(default_factory=dict, description="Config specifications")]
    default_agent_config: Annotated[dict[str, Any], Field(default_factory=dict, description="Default config values")]


class MCPServer:
    """
    MCP server bridging Swiss AI Agent Protocol with Model Context Protocol.

    Exposes AI Hub agents as MCP tools, enabling external clients like Claude Code,
    Cursor, and VS Code extensions to interact with agents.
    """

    def __init__(self, settings: MCPSettings | None = None) -> None:
        self._settings = settings or MCPSettings(REQUIRE_AUTH=False)
        self._mcp: FastMCP | None = None
        self._agent_registry: dict[str, AgentMetadata] = {}

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

        self._register_resources()

        logger.info("FastMCP instance created: Swiss AI Hub Agents")
        return self._mcp

    def _register_resources(self) -> None:
        """Register static MCP resources for agent listing."""

        @self.mcp.resource("agents://list")
        async def list_agents() -> dict[str, Any]:
            """List all available agents with their metadata."""
            return {
                "agents": [agent.model_dump() for agent in self._agent_registry.values()],
                "count": len(self._agent_registry),
            }

        @self.mcp.resource("agents://{agent_class}")
        async def get_agent(agent_class: str) -> dict[str, Any]:
            """Get metadata for a specific agent class."""
            if agent_class not in self._agent_registry:
                return {"error": f"Agent '{agent_class}' not found"}
            return self._agent_registry[agent_class].model_dump()

        logger.debug("MCP resources registered")

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
        """Register an agent discovered via SAAP."""
        self._agent_registry[agent_class] = AgentMetadata(
            agent_class=agent_class,
            is_conversational=is_conversational,
            start_events=[EventSpec(**e) for e in start_events],
            stop_events=[EventSpec(**e) for e in stop_events],
            hitl_request_events=[EventSpec(**e) for e in hitl_request_events],
            hitl_response_events=[EventSpec(**e) for e in hitl_response_events],
            agent_config_specs=agent_config_specs,
            default_agent_config=default_agent_config,
        )
        logger.info(f"Agent registered: {agent_class}")

    def unregister_agent(self, agent_class: str) -> None:
        """Remove an agent from the registry."""
        if agent_class in self._agent_registry:
            del self._agent_registry[agent_class]
            logger.info(f"Agent unregistered: {agent_class}")

    def is_agent_registered(self, agent_class: str) -> bool:
        """Check if an agent is registered."""
        return agent_class in self._agent_registry

    def get_registered_agents(self) -> list[str]:
        """Get list of registered agent class names."""
        return list(self._agent_registry.keys())

    def get_agent_metadata(self, agent_class: str) -> AgentMetadata | None:
        """Get metadata for a specific agent."""
        return self._agent_registry.get(agent_class)
