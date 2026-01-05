import logging
from typing import Any

from aihub_mcp.server.MCPServer import MCPServer

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """
    Manages MCP resources for agent metadata.

    Exposes agent information as browsable MCP resources. Resources are registered
    once and remain available; agent availability is checked via MCPServer.
    """

    def __init__(self, mcp_server: MCPServer) -> None:
        self._mcp_server = mcp_server

    def register_agent_resources(
        self,
        agent_class: str,
        agent_metadata: dict[str, Any],
    ) -> None:
        """Register MCP resources for a discovered agent."""
        mcp = self._mcp_server.mcp

        config_uri = f"agents://{agent_class}/config"
        events_uri = f"agents://{agent_class}/events"

        @mcp.resource(config_uri)
        async def get_agent_config() -> dict[str, Any]:
            """Get configuration schema for the agent."""
            config: dict[str, Any] = agent_metadata.get("agent_config_specs", {})
            return config

        @mcp.resource(events_uri)
        async def get_agent_events() -> dict[str, Any]:
            """Get supported events for the agent."""
            return {
                "start_events": agent_metadata.get("start_events", []),
                "stop_events": agent_metadata.get("stop_events", []),
                "hitl_request_events": agent_metadata.get("hitl_request_events", []),
                "hitl_response_events": agent_metadata.get("hitl_response_events", []),
            }

        logger.debug(f"Registered resources for agent: {agent_class}")
