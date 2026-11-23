import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Any

from openinference.semconv.trace import OpenInferenceMimeTypeValues, OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry.trace import Span, StatusCode
from swiss_ai_hub.core.infrastructure import get_tracer
from swiss_ai_hub.core.mcp import McpClientConfig

TOOLS_CALL_METHOD = "tools/call"
RESOURCES_READ_METHOD = "resources/read"


class McpCallSpan:
    """
    Traces one MCP call as a tool, so each call shows in Langfuse with its arguments and result.

    FastMCP traces the protocol request itself, but its spans carry no OpenInference kind, so the collector keeps them
    out of Langfuse, and they record neither arguments nor result. Opened as the current span, this one becomes their
    parent, and the cloud trace backend shows the whole chain. The connection's credentials are never recorded.
    """

    @staticmethod
    @contextmanager
    def open(
        server: Annotated[McpClientConfig, "The connection the call goes to"],
        method: Annotated[str, "The MCP method, TOOLS_CALL_METHOD or RESOURCES_READ_METHOD"],
        name: Annotated[str, "The tool the model called"],
        arguments: Annotated[dict[str, Any], "The arguments the model passed"],
    ) -> Iterator[Span]:
        parameters = json.dumps(arguments, default=str)
        with get_tracer(__name__).start_as_current_span(
            f"{server.name}.{name}",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
                SpanAttributes.TOOL_NAME: name,
                SpanAttributes.TOOL_PARAMETERS: parameters,
                SpanAttributes.INPUT_VALUE: parameters,
                SpanAttributes.INPUT_MIME_TYPE: OpenInferenceMimeTypeValues.JSON.value,
                "mcp.server.name": server.name,
                "mcp.auth_mode": str(server.auth_mode),
                "mcp.method.name": method,
            },
        ) as span:
            yield span

    @staticmethod
    def close(span: Span, text: Annotated[str, "The result as the model reads it"], is_error: bool) -> None:
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, text)
        if is_error:
            span.set_status(StatusCode.ERROR, text)
        else:
            span.set_status(StatusCode.OK)
