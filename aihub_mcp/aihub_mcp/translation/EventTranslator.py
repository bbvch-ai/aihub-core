import asyncio
import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from fastmcp import Context

from aihub_mcp.tracing.MCPTracer import MCPTracer
from aihub_mcp.translation.ElicitationHandler import ElicitationHandler
from aihub_mcp.translation.ProgressStreamer import ProgressStreamer
from aihub_mcp.translation.SamplingBridge import SamplingBridge

if TYPE_CHECKING:
    from aihub_mcp.translation.HITLPendingStore import HITLPendingStore

logger = logging.getLogger(__name__)

# Special marker for pending HITL responses
HITL_PENDING_MARKER = "__HITL_PENDING__"

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

    Bridges MCP tool invocations to SAAP events and streams agent responses back
    as MCP progress notifications.
    """

    def __init__(
        self,
        nats_url: str,
        elicitation_handler: ElicitationHandler | None = None,
        progress_streamer: ProgressStreamer | None = None,
        sampling_bridge: SamplingBridge | None = None,
        tracer: MCPTracer | None = None,
        hitl_pending_store: "HITLPendingStore | None" = None,
        agent_timeout_seconds: float = 300.0,
        mask_sensitive_data: bool = True,
    ) -> None:
        self._nats_url = nats_url
        self._elicitation_handler = elicitation_handler
        self._progress_streamer = progress_streamer
        self._sampling_bridge = sampling_bridge
        self._tracer = tracer
        self._hitl_pending_store = hitl_pending_store
        self._agent_timeout = agent_timeout_seconds
        self._mask_sensitive_data = mask_sensitive_data

        self._nc: Any = None
        self._js: Any = None
        self._js_publisher: JSPublisher | None = None

    def set_hitl_pending_store(self, store: "HITLPendingStore") -> None:
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
                {"thread_id": thread_id, "display_id": display_id, "run_id": run_id},
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

        result_future: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        accumulated_content: list[str] = []

        async def handle_display_event(msg: Any) -> None:
            try:
                event = json.loads(msg.data.decode())
                event_type = event.get("_event_name", "")

                if "ChunkEvent" in event_type:
                    content = event.get("content", "")
                    accumulated_content.append(content)
                    if self._progress_streamer:
                        await self._progress_streamer.stream_chunk(ctx, content)

                elif "ThoughtEvent" in event_type:
                    reasoning = event.get("reasoning_content", "")
                    if reasoning and self._progress_streamer:
                        await self._progress_streamer.stream_thought(ctx, reasoning)

                elif "HumanInTheLoop" in event_type and "Request" in event_type:
                    hitl_type = event.get("hitl_type", "input")
                    logger.debug(f"HITL request received: type={hitl_type}")
                    if self._tracer and span:
                        self._tracer.add_event(
                            span,
                            "hitl_request",
                            {"hitl_type": hitl_type},
                        )

                    if self._elicitation_handler:
                        elicit_result = await self._elicitation_handler.handle_request(ctx, event)

                        if elicit_result.success and elicit_result.response is not None:
                            # Elicitation worked - publish response and continue
                            await self._publish_hitl_response(
                                agent_class=agent_class,
                                agent_id=agent_id,
                                thread_id=thread_id,
                                display_id=display_id,
                                run_id=run_id,
                                request_event=event,
                                response=elicit_result.response,
                            )
                        else:
                            # Elicitation not supported - use two-phase fallback
                            request_id = f"hitl_{uuid.uuid4().hex[:12]}"
                            logger.info(f"Elicitation not supported, using fallback: {request_id}")

                            if self._hitl_pending_store:
                                # Store context for later retrieval
                                await self._hitl_pending_store.store_pending(
                                    request_id=request_id,
                                    agent_class=agent_class,
                                    thread_id=thread_id,
                                    display_id=display_id,
                                    run_id=run_id,
                                    request_event=event,
                                    hitl_type=hitl_type,
                                    accumulated_content=list(accumulated_content),
                                )

                                if self._tracer and span:
                                    self._tracer.add_event(span, "hitl_pending", {"request_id": request_id})

                                # Return pending response - this ends the tool call
                                pending_info = elicit_result.pending_info or {}
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
                                if not result_future.done():
                                    result_future.set_result(pending_response)
                            else:
                                # No store configured - fall back to old behavior
                                logger.warning("HITL pending store not configured, using fallback response")
                                await self._publish_hitl_response(
                                    agent_class=agent_class,
                                    agent_id=agent_id,
                                    thread_id=thread_id,
                                    display_id=display_id,
                                    run_id=run_id,
                                    request_event=event,
                                    response="[Elicitation not supported by client]",
                                )
                    else:
                        await ctx.warning("HITL request received but no handler configured")

                elif "SamplingRequestEvent" in event_type:
                    if self._tracer and span:
                        self._tracer.add_event(
                            span,
                            "sampling_request",
                            {"message_count": len(event.get("messages", []))},
                        )

                    if self._sampling_bridge:
                        try:
                            sampling_response = await self._sampling_bridge.handle_sampling_request(ctx, event)
                            await self._publish_sampling_response(
                                agent_class=agent_class,
                                agent_id=agent_id,
                                thread_id=thread_id,
                                display_id=display_id,
                                run_id=run_id,
                                request_event=event,
                                response=sampling_response,
                            )
                        except Exception as e:
                            logger.error(f"Sampling failed: {e}")
                            await ctx.error(f"LLM sampling failed: {e}")
                    else:
                        await ctx.warning("Sampling request received but no handler configured")

                elif "StopEvent" in event_type:
                    final_content = "".join(accumulated_content)
                    if not result_future.done():
                        result_future.set_result(final_content or "Agent completed successfully")

                elif "ExceptionEvent" in event_type:
                    error_msg = event.get("message", "Unknown error")
                    if not result_future.done():
                        result_future.set_exception(RuntimeError(error_msg))

            except Exception as e:
                logger.error(f"Error handling display event: {e}")

        sub = await self._nc.subscribe(display_subject, cb=handle_display_event)

        try:
            event = BaseEvent.deserialize_event(start_event)
            await self._js_publisher.publish_event(event, subject)

            if self._tracer and span:
                self._tracer.add_event(span, "event_published", {"subject": subject})

            result = await asyncio.wait_for(result_future, timeout=self._agent_timeout)

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

        # Retrieve stored context
        pending_context = await self._hitl_pending_store.get_pending(request_id)
        if not pending_context:
            raise ValueError(f"Pending HITL request not found or expired: {request_id}")

        agent_class = pending_context["agent_class"]
        thread_id = pending_context["thread_id"]
        display_id = pending_context["display_id"]
        run_id = pending_context["run_id"]
        request_event = pending_context["request_event"]
        hitl_type = pending_context["hitl_type"]
        accumulated_content = pending_context.get("accumulated_content", [])

        logger.info(f"Resuming HITL request {request_id}: agent={agent_class}, run={run_id}")

        await ctx.info(f"Resuming agent execution after HITL response: {request_id}")

        # Parse response based on hitl_type
        if hitl_type == "confirmation":
            parsed_response: str | bool = response.lower() in ("yes", "true", "1", "y")
        else:
            parsed_response = response

        # Generate new agent_id for this phase (agent uses its configured ID anyway)
        agent_id = f"mcp_{uuid.uuid4().hex[:8]}"

        # Start tracing span
        span = None
        if self._tracer:
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

        # Subscribe to display events before publishing response
        display_subject = self._build_display_subscription_pattern(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
        )

        result_future: asyncio.Future[str] = asyncio.get_event_loop().create_future()

        async def handle_display_event(msg: Any) -> None:
            try:
                event = json.loads(msg.data.decode())
                event_type = event.get("_event_name", "")
                logger.debug(f"Resume phase received event: {event_type}")

                if "ChunkEvent" in event_type:
                    content = event.get("content", "")
                    accumulated_content.append(content)
                    if self._progress_streamer:
                        await self._progress_streamer.stream_chunk(ctx, content)

                elif "ThoughtEvent" in event_type:
                    reasoning = event.get("reasoning_content", "")
                    if reasoning and self._progress_streamer:
                        await self._progress_streamer.stream_thought(ctx, reasoning)

                elif "StopEvent" in event_type:
                    final_content = "".join(accumulated_content)
                    if not result_future.done():
                        result_future.set_result(final_content or "Agent completed successfully")

                elif "ExceptionEvent" in event_type:
                    error_msg = event.get("message", "Unknown error")
                    if not result_future.done():
                        result_future.set_exception(RuntimeError(error_msg))

                elif "HumanInTheLoop" in event_type and "Request" in event_type:
                    # Another HITL request - this would need another two-phase flow
                    # For now, we don't support nested HITL in the resume phase
                    logger.warning("Nested HITL request during resume - not supported")
                    await ctx.warning(
                        "Agent requested additional human input during resume. "
                        "This is not supported in the two-phase flow."
                    )

            except Exception as e:
                logger.error(f"Error handling display event during resume: {e}")

        sub = await self._nc.subscribe(display_subject, cb=handle_display_event)
        logger.debug(f"Resume phase subscribed to: {display_subject}")

        try:
            # Publish the HITL response
            await self._publish_hitl_response(
                agent_class=agent_class,
                agent_id=agent_id,
                thread_id=thread_id,
                display_id=display_id,
                run_id=run_id,
                request_event=request_event,
                response=parsed_response,
            )

            # Wait for agent completion
            result = await asyncio.wait_for(result_future, timeout=self._agent_timeout)

            if self._tracer and span:
                self._tracer.end_span(span, success=True)

            # Clean up stored context
            await self._hitl_pending_store.remove_pending(request_id)

            return result

        except TimeoutError:
            error_msg = f"Agent execution timed out after {self._agent_timeout} seconds"
            if self._tracer and span:
                self._tracer.end_span(span, success=False, error_message=error_msg)
            # Clean up stored context even on timeout
            await self._hitl_pending_store.remove_pending(request_id)
            return error_msg

        except Exception as e:
            if self._tracer and span:
                self._tracer.end_span(span, success=False, error_message=str(e))
            raise

        finally:
            await sub.unsubscribe()
            logger.info(f"Resume phase completed: request_id={request_id}")
