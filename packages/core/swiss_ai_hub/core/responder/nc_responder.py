import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription
from nats.errors import BadSubscriptionError, ConnectionDrainingError
from opentelemetry import context, trace

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import get_tracer
from swiss_ai_hub.core.responder.abstract_responder import AbstractResponder, TRequest, TResponse
from swiss_ai_hub.core.tracing.nats_trace_context_propagator import NATSTraceContextPropagator

logger = logging.getLogger(__name__)


class NCResponder(AbstractResponder[TRequest, TResponse]):
    """
    NATS Core implementation of request-reply responder.

    Subscribes to a subject and responds to requests using msg.respond().
    Includes OpenTelemetry tracing and error handling.

    ### Example Usage:
    ```python
    async def handle_config_request(request: FetchConfigRequest, subject: str) -> FetchConfigResponse:
        config = await get_agent_config(request.agent_class, request.agent_id)
        return FetchConfigResponse(config=config)

    responder = NCResponder[FetchConfigRequest, FetchConfigResponse](
        name="AgentConfig",
        nc=nats_client,
        subject="aihub.rpc.config.agent.*.*",
        request_cls=FetchConfigRequest,
        handler=handle_config_request,
    )
    await responder.start()
    ```
    """

    def __init__(
        self,
        name: Annotated[str, "Name of the responder shown in otel"],
        nc: Annotated[NATS, "NATS client"],
        subject: Annotated[str, "NATS subject to listen on (supports wildcards)"],
        request_cls: Annotated[type[TRequest], "Request class for deserialization"],
        handler: Annotated[
            Callable[[TRequest, str], Awaitable[TResponse]],
            "Handler function: (request, subject) -> response",
        ],
    ):
        super().__init__(name, nc, subject, request_cls, handler, protocol="NATS")
        self._subscription: Subscription | None = None
        self._background_tasks: set[asyncio.Task[Any]] = set()

    async def start(self) -> None:
        """Start listening for requests on the configured subject."""
        logger.info(f"{self.name} starting on subject: {self.subject}")
        self._subscription = await self.nc.subscribe(self.subject, cb=self._message_handler)
        logger.info(f"{self.name} started successfully")

    async def stop(self) -> None:
        """Stop listening and clean up resources."""
        logger.info(f"{self.name} stopping...")

        if self._subscription:
            try:
                await self._subscription.unsubscribe()
            except (BadSubscriptionError, ConnectionDrainingError):
                logger.debug(f"{self.name} subscription was already unsubscribed")
            self._subscription = None

        # Wait for background tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

        logger.info(f"{self.name} stopped")

    async def _message_handler(self, msg: Msg) -> None:
        """Handle incoming request message by spawning a task."""
        task = asyncio.create_task(self._process_request(msg))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _process_request(self, msg: Msg) -> None:
        """Process a single request and send response."""
        tracer = get_tracer(__name__)

        headers = getattr(msg, "headers", {}) or {}
        parent_context = context.get_current()

        if headers:
            try:
                parent_context = NATSTraceContextPropagator.extract_and_activate_trace_context(headers)
            except Exception as e:
                logger.warning(f"{self.name} failed to extract trace context from headers: {e}")

        with tracer.start_as_current_span(
            f"{self.name}.respond",
            context=parent_context,
            kind=trace.SpanKind.SERVER,
            attributes={
                "messaging.system": "nats",
                "messaging.destination": msg.subject,
                "messaging.operation": "respond",
                "rpc.request_type": self.request_cls.__name__,
            },
        ) as span:
            try:
                # Deserialize request
                request = self.request_cls.model_validate_json(msg.data)
                logger.debug(f"{self.name} received request on {msg.subject}")

                response = await self.handler(request, msg.subject)

                # Serialize and send response
                # Note: NATS Core msg.respond() doesn't support headers, so trace context
                # cannot be propagated in the response. Tracing is maintained through the
                # span context on the responder side.
                serialized = response.model_dump_json()
                await msg.respond(serialized.encode())

                span.set_attribute("rpc.success", True)
                logger.debug(f"{self.name} sent response on {msg.subject}")

            except Exception as e:
                span.set_attribute("rpc.success", False)
                span.record_exception(e)
                logger.exception(f"{self.name} failed to handle request on {msg.subject}: {e}")

                error_response = {"error": str(e), "error_type": type(e).__name__}
                try:
                    await msg.respond(json.dumps(error_response).encode())
                except Exception:
                    logger.exception(f"{self.name} failed to send error response")
