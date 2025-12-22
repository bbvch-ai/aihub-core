"""Service for discovering agents via NATS and registering them as MCP tools."""

import asyncio
import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aihub_mcp.server.AgentToolRegistry import AgentToolRegistry
    from aihub_mcp.server.MCPServer import MCPServer
    from aihub_mcp.server.ResourceRegistry import ResourceRegistry
    from aihub_mcp.settings.MCPSettings import MCPSettings

logger = logging.getLogger(__name__)


class AgentDiscoveryService:
    """
    Discovers AI Hub agents via NATS and registers them as MCP tools.

    This service:
    1. Subscribes to agent discovery events on NATS
    2. Broadcasts discovery requests periodically
    3. Collects discovery responses from running agents
    4. Registers each agent as an MCP tool via AgentToolRegistry
    5. Updates registrations when agents come online/offline
    """

    def __init__(
        self,
        settings: "MCPSettings",
        mcp_server: "MCPServer",
        tool_registry: "AgentToolRegistry",
        resource_registry: "ResourceRegistry",
    ) -> None:
        self._settings = settings
        self._mcp_server = mcp_server
        self._tool_registry = tool_registry
        self._resource_registry = resource_registry

        self._nc: Any = None  # NATS connection
        self._running = False
        self._discovery_task: asyncio.Task[None] | None = None
        self._last_discovered: dict[str, float] = {}  # agent_class -> timestamp

    async def start(self) -> None:
        """Start the discovery service."""
        import nats

        self._nc = await nats.connect(self._settings.NATS_URL)
        self._running = True

        # Subscribe to discovery responses
        await self._nc.subscribe(
            "aihub.agents.discovery.response.call.*.*",
            cb=self._handle_discovery_response,
        )

        # Start periodic discovery
        self._discovery_task = asyncio.create_task(self._discovery_loop())

        # Trigger initial discovery
        await self._broadcast_discovery_request()

        logger.info("Agent discovery service started")

    async def stop(self) -> None:
        """Stop the discovery service."""
        self._running = False

        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass

        if self._nc:
            await self._nc.close()

        logger.info("Agent discovery service stopped")

    async def _discovery_loop(self) -> None:
        """Periodically broadcast discovery requests."""
        while self._running:
            try:
                await asyncio.sleep(self._settings.DISCOVERY_INTERVAL_SECONDS)
                await self._broadcast_discovery_request()
                self._cleanup_stale_agents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")

    async def _broadcast_discovery_request(self) -> None:
        """Broadcast a discovery request to all agents."""
        request_id = uuid.uuid4().hex[:12]
        subject = f"aihub.agents.discovery.request.{request_id}.call.{request_id}"

        event = {
            "event_id": str(uuid.uuid4()),
            "created_at": time.time_ns(),
            "_event_name": "ClassDiscoveryRequestEvent",
            "_parent_event_names": ["BaseEvent", "ClassDiscoveryRequestEvent"],
        }

        await self._nc.publish(subject, json.dumps(event).encode())
        logger.debug(f"Broadcast discovery request: {request_id}")

    async def _handle_discovery_response(self, msg: Any) -> None:
        """Handle a discovery response from an agent."""
        try:
            data = json.loads(msg.data.decode())
            event_name = data.get("_event_name", "")

            if "AgentClassDiscoveryResponseEvent" not in event_name:
                return

            agent_class = data.get("agent_class")
            if not agent_class:
                return

            # Update last seen timestamp
            self._last_discovered[agent_class] = time.time()

            # Check if already registered
            if agent_class in self._mcp_server._agent_registry:
                logger.debug(f"Agent already registered: {agent_class}")
                return

            # Register the agent
            self._register_agent(data)

        except Exception as e:
            logger.error(f"Error handling discovery response: {e}")

    def _register_agent(self, discovery_data: dict[str, Any]) -> None:
        """Register a discovered agent as MCP tool and resources."""
        agent_class = discovery_data.get("agent_class", "")
        is_conversational = discovery_data.get("is_conversational", False)
        start_events = discovery_data.get("start_events", [])
        stop_events = discovery_data.get("stop_events", [])
        hitl_request_events = discovery_data.get("hitl_request_events", [])
        hitl_response_events = discovery_data.get("hitl_response_events", [])
        agent_config_specs = discovery_data.get("agent_config_specs", {})
        default_agent_config = discovery_data.get("default_agent_config", {})

        # Register with MCP server
        self._mcp_server.register_agent(
            agent_class=agent_class,
            is_conversational=is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            hitl_request_events=hitl_request_events,
            hitl_response_events=hitl_response_events,
            agent_config_specs=agent_config_specs,
            default_agent_config=default_agent_config,
        )

        # Register MCP tools
        self._tool_registry.register_agent_tools(
            agent_class=agent_class,
            start_events=start_events,
            is_conversational=is_conversational,
        )

        # Register MCP resources
        self._resource_registry.register_agent_resources(
            agent_class=agent_class,
            agent_metadata=discovery_data,
        )

        logger.info(
            f"Registered agent: {agent_class} "
            f"(conversational={is_conversational}, "
            f"start_events={len(start_events)}, "
            f"hitl_events={len(hitl_request_events)})"
        )

    def _cleanup_stale_agents(self) -> None:
        """Remove agents that haven't been seen recently."""
        stale_threshold = self._settings.DISCOVERY_INTERVAL_SECONDS * 3
        current_time = time.time()

        stale_agents = [
            agent_class
            for agent_class, last_seen in self._last_discovered.items()
            if current_time - last_seen > stale_threshold
        ]

        for agent_class in stale_agents:
            self._mcp_server.unregister_agent(agent_class)
            self._tool_registry.unregister_agent_tools(agent_class)
            del self._last_discovered[agent_class]
            logger.info(f"Removed stale agent: {agent_class}")

    async def discover_now(self) -> dict[str, Any]:
        """Trigger immediate discovery and return results."""
        await self._broadcast_discovery_request()

        # Wait for responses
        await asyncio.sleep(self._settings.DISCOVERY_TIMEOUT_SECONDS)

        return {
            "agents": list(self._mcp_server._agent_registry.keys()),
            "count": len(self._mcp_server._agent_registry),
        }
