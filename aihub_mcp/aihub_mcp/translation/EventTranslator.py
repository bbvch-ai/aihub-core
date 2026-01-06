import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from fastmcp import Context
from opentelemetry.trace import Span

from aihub_mcp.tracing.MCPTracer import MCPTracer
from aihub_mcp.translation.ElicitationHandler import ElicitationHandler
from aihub_mcp.translation.ProgressStreamer import ProgressStreamer
from aihub_mcp.translation.SamplingBridge import SamplingBridge

if TYPE_CHECKING:
    from aihub_mcp.translation.HITLPendingStore import HITLPendingStoreInterface

logger = logging.getLogger(__name__)

DEFAULT_USER_IDENTITY = {
    "id": "anonymous",
    "name": "Anonymous (No Auth)",
    "email": "anonymous@aihub.local",
    "roles": ["user"],
}


@dataclass
class ExecutionContext:
    """Holds state for a single agent execution, reducing parameter passing."""

    agent_class: str
    agent_id: str
    thread_id: str
    display_id: str
    run_id: str
    ctx: Context
    result_future: asyncio.Future[str]
    accumulated_content: list[str] = field(default_factory=list)
    span: Span | None = None
    allow_hitl_fallback: bool = True


class EventTranslator:
    """
    Translates between Swiss AI Agent Protocol (SAAP) events and MCP protocol.

    This class exists because MCP clients (like Claude Code) speak a different language than
    our SAAP-based agents. Rather than modifying agents to understand MCP directly—which would
    tightly couple them to a specific client protocol—we translate at the boundary, allowing
    agents to remain protocol-agnostic while still being invocable via MCP.

    Key responsibilities:
    - Convert MCP tool calls into SAAP events that trigger agent workflows
    - Subscribe to agent display events and stream them back as MCP progress notifications
    - Handle HITL (Human-in-the-Loop) requests through either elicitation or two-phase fallback
    - Manage the NATS connection lifecycle for each tool invocation
    """

    def __init__(
        self,
        nats_url: str,
        elicitation_handler: ElicitationHandler | None = None,
        progress_streamer: ProgressStreamer | None = None,
        sampling_bridge: SamplingBridge | None = None,
        tracer: MCPTracer | None = None,
        hitl_pending_store: "HITLPendingStoreInterface | None" = None,
    ) -> None:
        self._nats_url = nats_url
        self._elicitation_handler = elicitation_handler
        self._progress_streamer = progress_streamer
        self._sampling_bridge = sampling_bridge
        self._tracer = tracer
        self._hitl_pending_store = hitl_pending_store
        self._agent_timeout = 300.0  # 5 minutes

        self._nc: Any = None
        self._js: Any = None
        self._js_publisher: JSPublisher | None = None

    def set_hitl_pending_store(self, store: "HITLPendingStoreInterface") -> None:
        """Set the HITL pending store for two-phase fallback flow."""
        self._hitl_pending_store = store

    async def connect(self) -> None:
        """Establish connection to NATS server."""
        import nats

        self._nc = await nats.connect(self._nats_url)
        self._js = self._nc.jetstream()
        self._js_publisher = JSPublisher("MCPEventTranslator", self._js)
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
        """Execute an agent by translating MCP tool call to SAAP events."""
        identity = user_identity or DEFAULT_USER_IDENTITY

        agent_id = f"mcp_{uuid.uuid4().hex[:8]}"
        thread_id = f"mcp_thread_{uuid.uuid4().hex[:12]}"
        display_id = f"mcp_display_{uuid.uuid4().hex[:8]}"
        run_id = f"mcp_run_{uuid.uuid4().hex[:8]}"
        event_id = str(uuid.uuid4())

        if self._progress_streamer:
            self._progress_streamer.reset()

        await ctx.info(
            f"Starting agent execution: agent={agent_class}, "
            f"thread={thread_id}, run={run_id}, user={identity.get('id', 'unknown')}"
        )

        exec_ctx = ExecutionContext(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            ctx=ctx,
            result_future=asyncio.get_event_loop().create_future(),
            span=self._start_execution_span(
                tool_name or event_name,
                agent_class,
                identity,
                exec_ids={
                    "thread_id": thread_id,
                    "display_id": display_id,
                    "run_id": run_id,
                    "agent_id": agent_id,
                },
            ),
        )

        start_event = self._build_start_event(
            event_name=event_name,
            event_parents=event_parents,
            event_data=event_data,
            event_id=event_id,
            user_identity=identity,
        )

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

        display_subject = self._build_display_subscription_pattern(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
        )

        return await self._execute_with_subscription(exec_ctx, start_event, subject, display_subject)

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

        if "UserMessageEvent" in event_name:
            base_event["user"] = user_identity

            if "message" in event_data and "messages" not in event_data:
                message_content = event_data.pop("message")
                base_event["messages"] = [
                    {
                        "role": "user",
                        "additional_kwargs": {},
                        "blocks": [{"block_type": "text", "text": message_content}],
                    }
                ]

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
        return f"agent.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}"

    def _build_display_subscription_pattern(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
    ) -> str:
        """Build a NATS subject pattern for subscribing to display events."""
        # Wildcard for agent_id because agent uses its configured ID, not our MCP-generated one
        return f"agent.{agent_class}.*.{thread_id}.{display_id}.*.display_event.>"

    def _start_execution_span(
        self,
        tool_name: str,
        agent_class: str,
        identity: dict[str, Any],
        exec_ids: dict[str, str],
    ) -> Span | None:
        """Start a tracing span for agent execution."""
        if not self._tracer:
            return None

        user_id_value = identity.get("id")
        span = self._tracer.start_agent_execution_span(
            tool_name=tool_name,
            agent_class=agent_class,
            thread_id=exec_ids["thread_id"],
            run_id=exec_ids["run_id"],
            display_id=exec_ids["display_id"],
            agent_id=exec_ids["agent_id"],
            user_id=str(user_id_value) if user_id_value is not None else None,
        )
        self._tracer.add_event(span, "execution_started", exec_ids)
        return span

    async def _execute_with_subscription(
        self,
        exec_ctx: ExecutionContext,
        start_event: dict[str, Any],
        subject: str,
        display_subject: str,
    ) -> str:
        """Execute agent with NATS subscription for display events."""

        async def handle_display_event(msg: Any) -> None:
            try:
                event = json.loads(msg.data.decode())
                await self._dispatch_display_event(exec_ctx, event)
            except Exception as e:
                logger.error(f"Error handling display event: {e}")

        sub = await self._nc.subscribe(display_subject, cb=handle_display_event)

        try:
            event = BaseEvent.deserialize_event(start_event)
            await self._js_publisher.publish_event(event, subject)

            if self._tracer and exec_ctx.span:
                self._tracer.add_event(exec_ctx.span, "event_published", {"subject": subject})

            result = await asyncio.wait_for(exec_ctx.result_future, timeout=self._agent_timeout)

            if self._tracer and exec_ctx.span:
                self._tracer.end_span(exec_ctx.span, success=True)

            return result

        except TimeoutError:
            error_msg = f"Agent execution timed out after {self._agent_timeout} seconds"
            if self._tracer and exec_ctx.span:
                self._tracer.end_span(exec_ctx.span, success=False, error_message=error_msg)
            return error_msg

        except Exception as e:
            if self._tracer and exec_ctx.span:
                self._tracer.end_span(exec_ctx.span, success=False, error_message=str(e))
            raise

        finally:
            try:
                await sub.unsubscribe()
            except Exception as cleanup_error:
                logger.warning(f"Failed to unsubscribe from display events: {cleanup_error}")
            logger.info(f"Agent execution completed: thread={exec_ctx.thread_id}, run={exec_ctx.run_id}")

    async def _handle_chunk_event(self, exec_ctx: ExecutionContext, event: dict[str, Any]) -> None:
        """Handle a ChunkEvent by accumulating content and streaming progress."""
        content = event.get("content", "")
        exec_ctx.accumulated_content.append(content)
        if self._progress_streamer:
            await self._progress_streamer.stream_chunk(exec_ctx.ctx, content)

    async def _handle_thought_event(self, exec_ctx: ExecutionContext, event: dict[str, Any]) -> None:
        """Handle a ThoughtEvent by streaming reasoning content."""
        reasoning = event.get("reasoning_content", "")
        if reasoning and self._progress_streamer:
            await self._progress_streamer.stream_thought(exec_ctx.ctx, reasoning)

    def _handle_stop_event(self, exec_ctx: ExecutionContext) -> None:
        """Handle a StopEvent by resolving the result future."""
        final_content = "".join(exec_ctx.accumulated_content)
        if not exec_ctx.result_future.done():
            exec_ctx.result_future.set_result(final_content or "Agent completed successfully")

    def _handle_exception_event(self, exec_ctx: ExecutionContext, event: dict[str, Any]) -> None:
        """Handle an ExceptionEvent by rejecting the result future."""
        error_msg = event.get("message", "Unknown error")
        if not exec_ctx.result_future.done():
            exec_ctx.result_future.set_exception(RuntimeError(error_msg))

    async def _handle_sampling_request(self, exec_ctx: ExecutionContext, event: dict[str, Any]) -> None:
        """Handle a SamplingRequestEvent by routing to client LLM."""
        if self._tracer and exec_ctx.span:
            self._tracer.add_event(
                exec_ctx.span,
                "sampling_request",
                {"message_count": len(event.get("messages", []))},
            )

        if not self._sampling_bridge:
            await exec_ctx.ctx.warning("Sampling request received but no handler configured")
            return

        try:
            sampling_response = await self._sampling_bridge.handle_sampling_request(exec_ctx.ctx, event)
            await self._publish_sampling_response(
                agent_class=exec_ctx.agent_class,
                agent_id=exec_ctx.agent_id,
                thread_id=exec_ctx.thread_id,
                display_id=exec_ctx.display_id,
                run_id=exec_ctx.run_id,
                request_event=event,
                response=sampling_response,
            )
        except Exception as e:
            logger.error(f"Sampling failed: {e}")
            await exec_ctx.ctx.error(f"LLM sampling failed: {e}")

    async def _handle_hitl_request(self, exec_ctx: ExecutionContext, event: dict[str, Any]) -> None:
        """Handle a HumanInTheLoopRequestEvent via elicitation or two-phase fallback."""
        hitl_type = event.get("hitl_type", "input")
        logger.debug(f"HITL request received: type={hitl_type}")

        if self._tracer and exec_ctx.span:
            self._tracer.add_event(exec_ctx.span, "hitl_request", {"hitl_type": hitl_type})

        if not self._elicitation_handler:
            await exec_ctx.ctx.warning("HITL request received but no handler configured")
            return

        elicit_result = await self._elicitation_handler.handle_request(exec_ctx.ctx, event)

        if elicit_result.success and elicit_result.response is not None:
            await self._publish_hitl_response(
                agent_class=exec_ctx.agent_class,
                agent_id=exec_ctx.agent_id,
                thread_id=exec_ctx.thread_id,
                display_id=exec_ctx.display_id,
                run_id=exec_ctx.run_id,
                request_event=event,
                response=elicit_result.response,
            )
            return

        # Elicitation not supported - use two-phase fallback if allowed
        if not exec_ctx.allow_hitl_fallback:
            logger.warning("Nested HITL request during resume - not supported")
            await exec_ctx.ctx.warning(
                "Agent requested additional human input during resume. This is not supported in the two-phase flow."
            )
            return

        await self._handle_hitl_fallback(exec_ctx, event, hitl_type, elicit_result.pending_info)

    async def _handle_hitl_fallback(
        self,
        exec_ctx: ExecutionContext,
        event: dict[str, Any],
        hitl_type: str,
        pending_info: dict[str, Any] | None,
    ) -> None:
        """Handle HITL via two-phase fallback when elicitation is not supported."""
        request_id = f"hitl_{uuid.uuid4().hex[:12]}"
        logger.info(f"Elicitation not supported, using fallback: {request_id}")

        if not self._hitl_pending_store:
            logger.warning("HITL pending store not configured, using fallback response")
            await self._publish_hitl_response(
                agent_class=exec_ctx.agent_class,
                agent_id=exec_ctx.agent_id,
                thread_id=exec_ctx.thread_id,
                display_id=exec_ctx.display_id,
                run_id=exec_ctx.run_id,
                request_event=event,
                response="[Elicitation not supported by client]",
            )
            return

        await self._hitl_pending_store.store_pending(
            request_id=request_id,
            agent_class=exec_ctx.agent_class,
            thread_id=exec_ctx.thread_id,
            display_id=exec_ctx.display_id,
            run_id=exec_ctx.run_id,
            request_event=event,
            hitl_type=hitl_type,
            accumulated_content=list(exec_ctx.accumulated_content),
        )

        if self._tracer and exec_ctx.span:
            self._tracer.add_event(exec_ctx.span, "hitl_pending", {"request_id": request_id})

        pending_info = pending_info or {}
        pending_response = json.dumps(
            {
                "status": "hitl_pending",
                "request_id": request_id,
                "question": pending_info.get("question", ""),
                "hitl_type": hitl_type,
                "instruction": (
                    "Please ask the user this question, then call "
                    "submit_hitl_response with request_id and their answer."
                ),
            }
        )

        if not exec_ctx.result_future.done():
            exec_ctx.result_future.set_result(pending_response)

    async def _dispatch_display_event(self, exec_ctx: ExecutionContext, event: dict[str, Any]) -> None:
        """Route a display event to the appropriate handler based on event type."""
        event_type = event.get("_event_name", "")

        if "ChunkEvent" in event_type:
            await self._handle_chunk_event(exec_ctx, event)
        elif "ThoughtEvent" in event_type:
            await self._handle_thought_event(exec_ctx, event)
        elif "HumanInTheLoop" in event_type and "Request" in event_type:
            await self._handle_hitl_request(exec_ctx, event)
        elif "SamplingRequestEvent" in event_type:
            await self._handle_sampling_request(exec_ctx, event)
        elif "StopEvent" in event_type:
            self._handle_stop_event(exec_ctx)
        elif "ExceptionEvent" in event_type:
            self._handle_exception_event(exec_ctx, event)

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

        event = BaseEvent.deserialize_event(response_event)
        await self._js_publisher.publish_event(event, subject)
        logger.info(f"Published HITL response to {subject}")

    async def _publish_sampling_response(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        request_event: dict[str, Any],
        response: str,
    ) -> None:
        """Publish a sampling response event back to NATS."""
        event_id = str(uuid.uuid4())
        event_name = "SamplingResponseEvent"
        event_parents = [
            "BaseEvent",
            "ControlEvent",
            "SamplingResponseEvent",
        ]

        response_event = {
            "event_id": event_id,
            "created_at": time.time_ns(),
            "_event_name": event_name,
            "_parent_event_names": event_parents,
            "content": response,
            "request_event_id": request_event.get("event_id"),
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

        event = BaseEvent.deserialize_event(response_event)
        await self._js_publisher.publish_event(event, subject)
        logger.info(f"Published sampling response to {subject}")

    async def resume_after_hitl(
        self,
        request_id: str,
        response: str,
        ctx: Context,
    ) -> str:
        """Resume agent execution after receiving a HITL response (Phase 2 of two-phase flow)."""
        if not self._hitl_pending_store:
            raise RuntimeError("HITL pending store not configured")

        pending_context = await self._hitl_pending_store.get_pending(request_id)
        if not pending_context:
            raise ValueError(f"Pending HITL request not found or expired: {request_id}")

        agent_class = pending_context["agent_class"]
        thread_id = pending_context["thread_id"]
        display_id = pending_context["display_id"]
        run_id = pending_context["run_id"]
        request_event = pending_context["request_event"]
        hitl_type = pending_context["hitl_type"]

        logger.info(f"Resuming HITL request {request_id}: agent={agent_class}, run={run_id}")
        await ctx.info(f"Resuming agent execution after HITL response: {request_id}")

        parsed_response = self._parse_hitl_response(response, hitl_type)
        agent_id = f"mcp_{uuid.uuid4().hex[:8]}"

        exec_ctx = ExecutionContext(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            ctx=ctx,
            result_future=asyncio.get_event_loop().create_future(),
            accumulated_content=list(pending_context.get("accumulated_content", [])),
            span=self._start_resume_span(agent_class, agent_id, thread_id, display_id, run_id, request_id),
            allow_hitl_fallback=False,  # No nested HITL in resume phase
        )

        display_subject = self._build_display_subscription_pattern(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
        )

        return await self._resume_with_subscription(
            exec_ctx, request_id, request_event, parsed_response, display_subject
        )

    def _parse_hitl_response(self, response: str, hitl_type: str) -> str | bool:
        """Parse HITL response based on type."""
        if hitl_type == "confirmation":
            return response.lower() in ("yes", "true", "1", "y")
        return response

    def _start_resume_span(
        self,
        agent_class: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        request_id: str,
    ) -> Span | None:
        """Start a tracing span for HITL resume."""
        if not self._tracer:
            return None

        span = self._tracer.start_agent_execution_span(
            tool_name="submit_hitl_response",
            agent_class=agent_class,
            thread_id=thread_id,
            run_id=run_id,
            display_id=display_id,
            agent_id=agent_id,
            user_id=None,
        )
        self._tracer.add_event(span, "hitl_resumed", {"request_id": request_id})
        return span

    async def _resume_with_subscription(
        self,
        exec_ctx: ExecutionContext,
        request_id: str,
        request_event: dict[str, Any],
        parsed_response: str | bool,
        display_subject: str,
    ) -> str:
        """Resume agent execution with NATS subscription."""

        async def handle_display_event(msg: Any) -> None:
            try:
                event = json.loads(msg.data.decode())
                logger.debug(f"Resume phase received event: {event.get('_event_name', '')}")
                await self._dispatch_display_event(exec_ctx, event)
            except Exception as e:
                logger.error(f"Error handling display event during resume: {e}")

        sub = await self._nc.subscribe(display_subject, cb=handle_display_event)
        logger.debug(f"Resume phase subscribed to: {display_subject}")

        try:
            await self._publish_hitl_response(
                agent_class=exec_ctx.agent_class,
                agent_id=exec_ctx.agent_id,
                thread_id=exec_ctx.thread_id,
                display_id=exec_ctx.display_id,
                run_id=exec_ctx.run_id,
                request_event=request_event,
                response=parsed_response,
            )

            result = await asyncio.wait_for(exec_ctx.result_future, timeout=self._agent_timeout)

            if self._tracer and exec_ctx.span:
                self._tracer.end_span(exec_ctx.span, success=True)

            await self._hitl_pending_store.remove_pending(request_id)
            return result

        except TimeoutError:
            error_msg = f"Agent execution timed out after {self._agent_timeout} seconds"
            if self._tracer and exec_ctx.span:
                self._tracer.end_span(exec_ctx.span, success=False, error_message=error_msg)
            await self._hitl_pending_store.remove_pending(request_id)
            return error_msg

        except Exception as e:
            if self._tracer and exec_ctx.span:
                self._tracer.end_span(exec_ctx.span, success=False, error_message=str(e))
            raise

        finally:
            try:
                await sub.unsubscribe()
            except Exception as cleanup_error:
                logger.warning(f"Failed to unsubscribe during resume cleanup: {cleanup_error}")
            logger.info(f"Resume phase completed: request_id={request_id}")
