import logging
from typing import Any

from aihub_mcp.server.MCPServer import MCPServer

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """
    Manages MCP resources for agent metadata.

    Exposes agent information as browsable MCP resources:
    - agents://{agent_class}/config - Agent configuration schema
    - agents://{agent_class}/events - Supported events
    """

    def __init__(self, mcp_server: MCPServer) -> None:
        self._mcp_server = mcp_server
        self._registered_resources: dict[str, str] = {}  # resource_uri -> agent_class

    def register_agent_resources(
        self,
        agent_class: str,
        agent_metadata: dict[str, Any],
    ) -> None:
        """Register MCP resources for a discovered agent."""
        mcp = self._mcp_server.mcp

        config_uri = f"agents://{agent_class}/config"
        events_uri = f"agents://{agent_class}/events"

        # Skip if already registered
        if config_uri in self._registered_resources:
            logger.debug(f"Resources already registered for agent: {agent_class}")
            return

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

        self._registered_resources[config_uri] = agent_class
        self._registered_resources[events_uri] = agent_class

        logger.debug(f"Registered resources for agent: {agent_class}")

    def unregister_agent_resources(self, agent_class: str) -> None:
        """Remove all resources for an agent that went offline."""
        resources_to_remove = [uri for uri, ac in self._registered_resources.items() if ac == agent_class]

        for uri in resources_to_remove:
            del self._registered_resources[uri]
            logger.debug(f"Unregistered resource: {uri}")

        # Note: FastMCP doesn't support runtime resource removal
        # Resources will remain registered but associated agent may be unavailable

    def get_registered_resources(self) -> dict[str, str]:
        """Get mapping of registered resource URIs to agent classes."""
        return self._registered_resources.copy()
