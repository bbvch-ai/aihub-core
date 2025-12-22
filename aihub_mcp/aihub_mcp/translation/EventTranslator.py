"""SAAP to MCP event translation layer."""

import asyncio
import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from fastmcp import Context

if TYPE_CHECKING:
    from aihub_mcp.translation.ElicitationHandler import ElicitationHandler
    from aihub_mcp.translation.ProgressStreamer import ProgressStreamer
    from aihub_mcp.translation.SamplingBridge import SamplingBridge

logger = logging.getLogger(__name__)

# Synthetic user identity for MCP clients (no authentication context)
MCP_USER_IDENTITY = {
    "id": "mcp-client",
    "name": "MCP Client",
    "email": "mcp@localhost",
    "roles": ["user"],
}


class EventTranslator:
    """
    Translates between Swiss AI Agent Protocol (SAAP) events and MCP protocol.

    This is the core bridge between the two protocols, handling:
    - Tool invocation → UserMessageEvent/StartEvent
    - ChunkEvent/ThoughtEvent → Progress notifications
    - HumanInTheLoopRequestEvent → Elicitation request
    - StopEvent → Tool success response
    - ExceptionEvent → Tool error response
    """

    def __init__(
        self,
        nats_url: str,
        elicitation_handler: "ElicitationHandler | None" = None,
        progress_streamer: "ProgressStreamer | None" = None,
        sampling_bridge: "SamplingBridge | None" = None,
    ) -> None:
        self._nats_url = nats_url
        self._elicitation_handler = elicitation_handler
        self._progress_streamer = progress_streamer
        self._sampling_bridge = sampling_bridge

        self._nc: Any = None  # NATS connection
        self._js: Any = None  # JetStream context

    async def connect(self) -> None:
        """Establish connection to NATS server."""
        import nats

        self._nc = await nats.connect(self._nats_url)
        self._js = self._nc.jetstream()
        logger.info(f"Connected to NATS: {self._nats_url}")

    async def disconnect(self) -> None:
        """Close NATS connection."""
        if self._nc:
            await self._nc.close()
            logger.info("Disconnected from NATS")

    async def execute_agent(
        self,
        agent_class: str,
        event_name: str,
        event_parents: list[str],
        event_data: dict[str, Any],
        ctx: Context,
    ) -> str:
        """
        Execute an agent by translating MCP tool call to SAAP events.

        1. Creates a thread and run context
        2. Publishes the start event to NATS
        3. Subscribes to display events for progress
        4. Handles HITL requests via elicitation
        5. Returns final result on StopEvent/ExceptionEvent
        """
        # Generate identifiers for this execution
        agent_id = f"mcp_{uuid.uuid4().hex[:8]}"
        thread_id = f"mcp_{uuid.uuid4().hex[:12]}"
        display_id = f"d_{uuid.uuid4().hex[:8]}"
        run_id = f"r_{uuid.uuid4().hex[:8]}"
        event_id = str(uuid.uuid4())

        await ctx.info(f"Starting agent execution: thread={thread_id}")

        # Build the start event
        start_event = self._build_start_event(
            event_name=event_name,
            event_parents=event_parents,
            event_data=event_data,
            event_id=event_id,
        )

        # Build the NATS subject for publishing
        subject = self._build_subject(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            event_type="control_event",
            event_name=event_name,
            event_id=event_id,
        )

        # Subscribe to display events before publishing
        display_subject = self._build_display_subscription_pattern(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
        )

        result_future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        accumulated_content: list[str] = []

        async def handle_display_event(msg: Any) -> None:
            """Handle incoming display events."""
            try:
                event = json.loads(msg.data.decode())
                event_type = event.get("_event_name", "")

                # Handle ChunkEvent - stream progress
                if "ChunkEvent" in event_type:
                    content = event.get("content", "")
                    accumulated_content.append(content)
                    if self._progress_streamer:
                        await self._progress_streamer.stream_chunk(ctx, content)

                # Handle ThoughtEvent - stream reasoning
                elif "ThoughtEvent" in event_type:
                    reasoning = event.get("reasoning_content", "")
                    if reasoning and self._progress_streamer:
                        await self._progress_streamer.stream_thought(ctx, reasoning)

                # Handle HumanInTheLoopRequestEvent - elicitation
                elif "HumanInTheLoopRequestEvent" in event_type:
                    if self._elicitation_handler:
                        response = await self._elicitation_handler.handle_request(ctx, event)
                        # Publish response back to NATS
                        await self._publish_hitl_response(
                            agent_class=agent_class,
                            agent_id=agent_id,
                            thread_id=thread_id,
                            display_id=display_id,
                            run_id=run_id,
                            request_event=event,
                            response=response,
                        )
                    else:
                        await ctx.warning("HITL request received but no handler configured")

                # Handle StopEvent - completion
                elif "StopEvent" in event_type:
                    final_content = "".join(accumulated_content)
                    if not result_future.done():
                        result_future.set_result(final_content or "Agent completed successfully")

                # Handle ExceptionEvent - error
                elif "ExceptionEvent" in event_type:
                    error_msg = event.get("message", "Unknown error")
                    if not result_future.done():
                        result_future.set_exception(RuntimeError(error_msg))

            except Exception as e:
                logger.error(f"Error handling display event: {e}")

        # Subscribe to display events
        sub = await self._nc.subscribe(display_subject, cb=handle_display_event)

        try:
            # Publish the start event
            await self._js.publish(subject, json.dumps(start_event).encode())
            logger.info(f"Published start event to {subject}")

            # Wait for result with timeout
            result = await asyncio.wait_for(result_future, timeout=300.0)  # 5 minute timeout
            return result

        except TimeoutError:
            return "Agent execution timed out"
        finally:
            await sub.unsubscribe()

    def _build_start_event(
        self,
        event_name: str,
        event_parents: list[str],
        event_data: dict[str, Any],
        event_id: str,
    ) -> dict[str, Any]:
        """Build a SAAP start event from MCP tool parameters."""
        base_event = {
            "event_id": event_id,
            "created_at": time.time_ns(),
            "_event_name": event_name,
            "_parent_event_names": event_parents,
        }

        # Handle UserMessageEvent specifically - requires user identity and messages format
        if "UserMessageEvent" in event_name:
            base_event["user"] = MCP_USER_IDENTITY

            # Convert message string to proper messages format if needed
            if "message" in event_data and "messages" not in event_data:
                message_content = event_data.pop("message")
                base_event["messages"] = [
                    {
                        "role": "user",
                        "content": message_content,
                    }
                ]

        # Merge remaining event data
        base_event.update(event_data)
        return base_event

    def _build_subject(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        event_type: str,
        event_name: str,
        event_id: str,
    ) -> str:
        """Build a NATS subject for publishing events."""
        # Format: agent.<agent_class>.<agent_id>.<thread_id>.<display_id>.<run_id>.<event_type>.<event_name>.<event_id>
        return f"agent.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}"

    def _build_display_subscription_pattern(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
    ) -> str:
        """Build a NATS subject pattern for subscribing to display events."""
        # Subscribe to all display events for this display context
        # Format: agent.<agent_class>.<agent_id>.<thread_id>.<display_id>.<run_id>.display_event.<event_name>.<event_id>
        # Note: Use wildcard for agent_id because the actual agent uses its configured ID (e.g., "rag_dev_agent")
        # rather than the MCP-generated ID we used when publishing
        return f"agent.{agent_class}.*.{thread_id}.{display_id}.*.display_event.>"

    async def _publish_hitl_response(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        request_event: dict[str, Any],
        response: str | bool,
    ) -> None:
        """Publish a HITL response event back to NATS."""
        event_id = str(uuid.uuid4())

        # Determine response event type based on request type
        hitl_type = request_event.get("hitl_type", "input")
        if hitl_type == "confirmation":
            event_name = "HumanInTheLoopConfirmationResponseEvent"
            event_parents = [
                "BaseEvent",
                "ControlEvent",
                "DisplayEvent",
                "ControlAndDisplayEvent",
                "HumanInTheLoopResponseEvent",
                "HumanInTheLoopConfirmationResponseEvent",
            ]
        else:
            event_name = "HumanInTheLoopInputResponseEvent"
            event_parents = [
                "BaseEvent",
                "ControlEvent",
                "DisplayEvent",
                "ControlAndDisplayEvent",
                "HumanInTheLoopResponseEvent",
                "HumanInTheLoopInputResponseEvent",
            ]

        response_event = {
            "event_id": event_id,
            "created_at": time.time_ns(),
            "_event_name": event_name,
            "_parent_event_names": event_parents,
            "response": response,
            "request_event": request_event,
        }

        subject = self._build_subject(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            event_type="control_event",
            event_name=event_name,
            event_id=event_id,
        )

        await self._js.publish(subject, json.dumps(response_event).encode())
        logger.info(f"Published HITL response to {subject}")
