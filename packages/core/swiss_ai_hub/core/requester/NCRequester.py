import logging
from typing import Annotated

from nats.aio.client import Client as NATS
from nats.errors import TimeoutError as NatsTimeoutError

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.SmartTracer import get_tracer
from swiss_ai_hub.core.requester.AbstractRequester import AbstractRequester, TRequest, TResponse
from swiss_ai_hub.core.tracing.NATSMessageHeaders import NATSMessageHeaders

logger = logging.getLogger(__name__)


class NCRequester(AbstractRequester[TRequest, TResponse]):
    """
    NATS Core implementation of request-reply pattern.

    Uses nc.request() for synchronous request-response over NATS.
    Includes OpenTelemetry tracing and timeout handling.

    ### Example Usage:
    ```python
    requester = NCRequester[FetchConfigRequest, FetchConfigResponse](
        name="AgentConfig",
        nc=nats_client,
        response_cls=FetchConfigResponse,
    )

    response = await requester.request(
        FetchConfigRequest(agent_class="RAGAgent", agent_id="default"),
        subject="aihub.rpc.config.agent.RAGAgent.default",
    )
    ```
    """

    def __init__(
        self,
        name: Annotated[str, "Name of the requester shown in otel"],
        nc: Annotated[NATS, "NATS client"],
        response_cls: Annotated[type[TResponse], "Response class for deserialization"],
        default_timeout_ms: Annotated[int, "Default timeout in milliseconds"] = 5000,
    ):
        super().__init__(name, response_cls, protocol="NATS", default_timeout_ms=default_timeout_ms)
        self.nc = nc

    async def request(
        self,
        request: TRequest,
        subject: str,
        timeout_ms: int | None = None,
    ) -> TResponse:
        timeout = (timeout_ms or self.default_timeout_ms) / 1000.0  # Convert to seconds
        tracer = get_tracer(__name__)

        with tracer.start_as_current_span(
            f"{self.name}.request",
            attributes={
                "messaging.system": "nats",
                "messaging.destination": subject,
                "messaging.operation": "request",
                "rpc.request_type": request.__class__.__name__,
                "rpc.response_type": self.response_cls.__name__,
            },
        ) as span:
            try:
                # Serialize request
                serialized = request.model_dump_json()
                logger.debug(f"{self.name} sending request to {subject}: {serialized}")

                headers = NATSMessageHeaders().with_trace_context().to_dict()

                response_msg = await self.nc.request(
                    subject,
                    serialized.encode(),
                    timeout=timeout,
                    headers=headers,
                )

                # Deserialize response
                response = self.response_cls.model_validate_json(response_msg.data)

                span.set_attribute("rpc.success", True)
                logger.debug(f"{self.name} received response from {subject}")

                return response

            except NatsTimeoutError:
                span.set_attribute("rpc.success", False)
                span.set_attribute("rpc.error", "timeout")
                logger.warning(f"{self.name} request to {subject} timed out after {timeout}s")
                raise TimeoutError(f"Request to {subject} timed out after {timeout}s") from None

            except Exception as e:
                span.set_attribute("rpc.success", False)
                span.record_exception(e)
                logger.exception(f"{self.name} request to {subject} failed: {e}")
                raise
