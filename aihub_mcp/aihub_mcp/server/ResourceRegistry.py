"""MCP resource registry for agent metadata."""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aihub_mcp.server.MCPServer import MCPServer

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """
    Manages MCP resources for agent metadata.

    Exposes agent information as browsable MCP resources:
    - agents://list - List all agents
    - agents://{agent_class} - Agent class details
    - agents://{agent_class}/config - Agent configuration schema
    - agents://{agent_class}/events - Supported events
    """

    def __init__(self, mcp_server: "MCPServer") -> None:
        self._mcp_server = mcp_server

    def register_agent_resources(
        self,
        agent_class: str,
        agent_metadata: dict[str, Any],
    ) -> None:
        """
        Register MCP resources for a discovered agent.

        Creates resource templates for browsing agent details.
        """
        mcp = self._mcp_server.mcp

        # Register config resource
        @mcp.resource(f"agents://{agent_class}/config")
        async def get_agent_config() -> dict[str, Any]:
            """Get configuration schema for the agent."""
            config: dict[str, Any] = agent_metadata.get("agent_config_specs", {})
            return config

        # Register events resource
        @mcp.resource(f"agents://{agent_class}/events")
        async def get_agent_events() -> dict[str, Any]:
            """Get supported events for the agent."""
            return {
                "start_events": agent_metadata.get("start_events", []),
                "stop_events": agent_metadata.get("stop_events", []),
                "hitl_request_events": agent_metadata.get("hitl_request_events", []),
                "hitl_response_events": agent_metadata.get("hitl_response_events", []),
            }

        logger.debug(f"Registered resources for agent: {agent_class}")

    def get_all_agents_summary(self) -> list[dict[str, Any]]:
        """Get a summary of all registered agents for the list resource."""
        return [
            {
                "agent_class": agent_class,
                "is_conversational": metadata.get("is_conversational", False),
                "start_event_count": len(metadata.get("start_events", [])),
            }
            for agent_class, metadata in self._mcp_server._agent_registry.items()
        ]
