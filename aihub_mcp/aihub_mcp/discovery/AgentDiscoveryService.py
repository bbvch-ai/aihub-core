import asyncio
import contextlib
import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager

from aihub_mcp.discovery.PromptRegistry import PromptRegistry
from aihub_mcp.server.AgentToolRegistry import AgentToolRegistry
from aihub_mcp.server.MCPServer import MCPServer
from aihub_mcp.server.ResourceRegistry import ResourceRegistry

if TYPE_CHECKING:
    from aihub_mcp.tracing.MCPTracer import MCPTracer

logger = logging.getLogger(__name__)


class AgentDiscoveryService:
    """
    Discovers AI Hub agents via NATS and registers them as MCP tools.

    This service solves the problem of dynamic agent availability. Unlike static tool
    registration where tools are defined at startup, AI Hub agents can come and go at
    runtime—deployed, scaled, or taken offline independently. This service continuously
    monitors for agents and keeps the MCP tool registry in sync with what's actually
    available, preventing clients from invoking agents that have gone offline.

    The discovery mechanism uses NATS pub/sub to broadcast requests and collect responses,
    allowing agents running anywhere in the cluster to self-register their capabilities.
    Stale agents are automatically cleaned up when they stop responding to discovery pings.
    """

    def __init__(
        self,
        mcp_server: MCPServer,
        tool_registry: AgentToolRegistry,
        resource_registry: ResourceRegistry,
        prompt_registry: PromptRegistry,
        tracer: "MCPTracer | None" = None,
    ) -> None:
        self._mcp_server = mcp_server
        self._tool_registry = tool_registry
        self._resource_registry = resource_registry
        self._prompt_registry = prompt_registry
        self._tracer = tracer
        self._topic_manager = AgentTopicManager()

        self._nc: Any = None  # NATS connection
        self._running = False
        self._discovery_task: asyncio.Task[None] | None = None
        self._last_discovered: dict[str, float] = {}  # agent_class -> timestamp

    async def start(self) -> None:
        """Start the discovery service."""
        import nats

        self._nc = await nats.connect(NatsSettings().ENDPOINT)
        self._running = True

        # Subscribe to discovery responses using platform topic pattern
        # Pattern: class_discovery.agent.{agent_class}.*.response.{call_id}
        response_pattern = self._topic_manager.get_agent_class_discovery_subject_response(
            call_id="*",
            agent_class="*",
        )
        await self._nc.subscribe(
            response_pattern,
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
            with contextlib.suppress(asyncio.CancelledError):
                await self._discovery_task

        if self._nc:
            await self._nc.close()

        logger.info("Agent discovery service stopped")

    async def _discovery_loop(self) -> None:
        """Periodically broadcast discovery requests."""
        while self._running:
            try:
                await asyncio.sleep(30.0)  # Discovery interval
                await self._broadcast_discovery_request()
                self._cleanup_stale_agents()
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")

    async def _broadcast_discovery_request(self) -> None:
        """Broadcast a discovery request to all agents."""
        call_id = uuid.uuid4().hex[:12]

        span = None
        if self._tracer:
            span = self._tracer.start_discovery_span("broadcast", call_id)

        try:
            # Use platform topic manager to get correct subject
            # Pattern: class_discovery.agent.*.*.request.{call_id}
            subject = self._topic_manager.get_agent_class_discovery_subject_request(
                call_id=call_id,
                agent_class="*",
            )

            # Use proper ClassDiscoveryRequestEvent from aihub_lib
            event = ClassDiscoveryRequestEvent()

            await self._nc.publish(subject, event.model_dump_json().encode())
            logger.debug(f"Broadcast discovery request: {call_id} on {subject}")

            if self._tracer and span:
                self._tracer.end_span(span, success=True)
        except Exception as e:
            if self._tracer and span:
                self._tracer.end_span(span, success=False, error_message=str(e))
            raise

    async def _handle_discovery_response(self, msg: Any) -> None:
        """Handle a discovery response from an agent (NATS requires async callbacks)."""
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
            if self._mcp_server.is_agent_registered(agent_class):
                logger.debug(f"Agent already registered: {agent_class}")
                return

            # Register the agent (sync operation, yield control to event loop)
            self._register_agent(data)
            await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Error handling discovery response: {e}")

    def _register_agent(self, discovery_data: dict[str, Any]) -> None:
        """Register a discovered agent as MCP tool and resources."""
        agent_class = discovery_data.get("agent_class", "")

        span = None
        if self._tracer:
            span = self._tracer.start_agent_registration_span(agent_class)

        try:
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

            # Register MCP prompts
            self._prompt_registry.register_agent_prompts(
                agent_class=agent_class,
                is_conversational=is_conversational,
            )

            if self._tracer and span:
                self._tracer.add_event(
                    span,
                    "agent_registered",
                    {
                        "is_conversational": is_conversational,
                        "start_events_count": len(start_events),
                        "hitl_events_count": len(hitl_request_events),
                    },
                )
                self._tracer.end_span(span, success=True)

            logger.info(
                f"Registered agent: {agent_class} "
                f"(conversational={is_conversational}, "
                f"start_events={len(start_events)}, "
                f"hitl_events={len(hitl_request_events)})"
            )
        except Exception as e:
            if self._tracer and span:
                self._tracer.end_span(span, success=False, error_message=str(e))
            raise

    def _cleanup_stale_agents(self) -> None:
        """Mark agents that haven't been seen recently as unavailable."""
        stale_threshold = 90.0  # 3x discovery interval
        current_time = time.time()

        stale_agents = [
            agent_class
            for agent_class, last_seen in self._last_discovered.items()
            if current_time - last_seen > stale_threshold
        ]

        for agent_class in stale_agents:
            self._mcp_server.unregister_agent(agent_class)
            del self._last_discovered[agent_class]
            logger.info(f"Marked agent as unavailable: {agent_class}")

    async def discover_now(self) -> dict[str, Any]:
        """Trigger immediate discovery and return results."""
        await self._broadcast_discovery_request()

        # Wait for responses
        await asyncio.sleep(5.0)  # Discovery timeout

        agents = self._mcp_server.get_registered_agents()
        return {
            "agents": agents,
            "count": len(agents),
        }
