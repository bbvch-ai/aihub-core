"""SAAP to MCP event translation layer."""

import asyncio
import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from fastmcp import Context

if TYPE_CHECKING:
    from aihub_mcp.tracing.MCPTracer import MCPTracer
    from aihub_mcp.translation.ElicitationHandler import ElicitationHandler
    from aihub_mcp.translation.ProgressStreamer import ProgressStreamer
    from aihub_mcp.translation.SamplingBridge import SamplingBridge

logger = logging.getLogger(__name__)

# Default user identity when none provided (auth disabled)
DEFAULT_USER_IDENTITY = {
    "id": "anonymous",
    "name": "Anonymous (No Auth)",
    "email": "anonymous@aihub.local",
    "roles": ["user"],
    "source": "no_auth",
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

    Each invocation creates unique thread_id and run_id for proper tracing in Phoenix.
    """

    def __init__(
        self,
        nats_url: str,
        elicitation_handler: "ElicitationHandler | None" = None,
        progress_streamer: "ProgressStreamer | None" = None,
        sampling_bridge: "SamplingBridge | None" = None,
        tracer: "MCPTracer | None" = None,
        agent_timeout_seconds: float = 300.0,
        mask_sensitive_data: bool = True,
    ) -> None:
        self._nats_url = nats_url
        self._elicitation_handler = elicitation_handler
        self._progress_streamer = progress_streamer
        self._sampling_bridge = sampling_bridge
        self._tracer = tracer
        self._agent_timeout = agent_timeout_seconds
        self._mask_sensitive_data = mask_sensitive_data

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
        user_identity: dict[str, Any] | None = None,
        tool_name: str | None = None,
    ) -> str:
        """
        Execute an agent by translating MCP tool call to SAAP events.

        1. Creates a thread and run context (unique per invocation)
        2. Starts an OpenTelemetry span with thread/run IDs for Phoenix
        3. Publishes the start event to NATS
        4. Subscribes to display events for progress
        5. Handles HITL requests via elicitation
        6. Returns final result on StopEvent/ExceptionEvent
        """
        # Use provided identity or default
        identity = user_identity or DEFAULT_USER_IDENTITY

        # Generate UNIQUE identifiers for THIS execution
        # Each MCP tool invocation gets its own thread_id and run_id
        agent_id = f"mcp_{uuid.uuid4().hex[:8]}"
        thread_id = f"mcp_thread_{uuid.uuid4().hex[:12]}"
        display_id = f"mcp_display_{uuid.uuid4().hex[:8]}"
        run_id = f"mcp_run_{uuid.uuid4().hex[:8]}"
        event_id = str(uuid.uuid4())

        await ctx.info(
            f"Starting agent execution: agent={agent_class}, "
            f"thread={thread_id}, run={run_id}, user={identity.get('id', 'unknown')}"
        )

        # Start tracing span with full context for Phoenix
        span = None
        if self._tracer:
            user_id_value = identity.get("id")
            span = self._tracer.start_agent_execution_span(
                tool_name=tool_name or event_name,
                agent_class=agent_class,
                thread_id=thread_id,
                run_id=run_id,
                display_id=display_id,
                agent_id=agent_id,
                user_id=str(user_id_value) if user_id_value is not None else None,
            )

        if self._tracer and span:
            self._tracer.add_event(
                span,
                "execution_started",
                {
                    "thread_id": thread_id,
                    "display_id": display_id,
                    "run_id": run_id,
                },
            )

        # Build the start event
        start_event = self._build_start_event(
            event_name=event_name,
            event_parents=event_parents,
            event_data=event_data,
            event_id=event_id,
            user_identity=identity,
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
                    if self._tracer and span:
                        self._tracer.add_event(
                            span,
                            "hitl_request",
                            {
                                "hitl_type": event.get("hitl_type", "input"),
                            },
                        )

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

            if self._tracer and span:
                self._tracer.add_event(span, "event_published", {"subject": subject})

            # Wait for result with configurable timeout
            result = await asyncio.wait_for(result_future, timeout=self._agent_timeout)

            # End span with success
            if self._tracer and span:
                self._tracer.end_span(span, success=True)

            return result

        except TimeoutError:
            error_msg = f"Agent execution timed out after {self._agent_timeout} seconds"
            if self._tracer and span:
                self._tracer.end_span(span, success=False, error_message=error_msg)
            return error_msg

        except Exception as e:
            if self._tracer and span:
                self._tracer.end_span(span, success=False, error_message=str(e))
            raise

        finally:
            await sub.unsubscribe()
            logger.info(f"Agent execution completed: thread={thread_id}, run={run_id}")

    def _build_start_event(
        self,
        event_name: str,
        event_parents: list[str],
        event_data: dict[str, Any],
        event_id: str,
        user_identity: dict[str, Any],
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
            base_event["user"] = user_identity

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
