"""Each MCP call is traced as a tool, and a call the server refuses goes back to the model instead of ending the run."""

import json
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import SmartTracer
from swiss_ai_hub.core.mcp import McpClientConfig

from swiss_ai_hub.agent.mcp.mcp_resource_schemas import READ_MCP_RESOURCE_TOOL_NAME
from swiss_ai_hub.agent.mcp.mcp_tool_schemas import execute_single_tool_call

SERVER = McpClientConfig(name="echo-server", url="http://echo.example/mcp", auth_mode="api_key", api_key="sk-secret")


def _server() -> FastMCP:
    server = FastMCP("echo-server")

    @server.tool
    def echo(text: str) -> str:
        return f"echo: {text}"

    @server.tool
    def fail() -> str:
        raise ToolError("the backend is down")

    @server.resource("doc://readme")
    def readme() -> str:
        return "read me first"

    return server


@pytest.fixture
def exporter() -> Iterator[InMemorySpanExporter]:
    """A provider of its own for both our span and FastMCP's, so the test neither depends on nor installs the global
    one."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with (
        patch(
            "swiss_ai_hub.agent.mcp.mcp_call_span.get_tracer",
            return_value=SmartTracer(provider.get_tracer("test")),
        ),
        patch("fastmcp.client.telemetry.get_tracer", return_value=provider.get_tracer("fastmcp")),
    ):
        yield exporter


def _tool_spans(exporter: InMemorySpanExporter) -> list[ReadableSpan]:
    return [
        span
        for span in exporter.get_finished_spans()
        if span.attributes.get(SpanAttributes.OPENINFERENCE_SPAN_KIND) == OpenInferenceSpanKindValues.TOOL.value
    ]


async def _call(tool_name: str, arguments: dict) -> str:
    async with Client(_server()) as client:
        message = await execute_single_tool_call(
            client, server=SERVER, tool_call_id="call-1", tool_name=tool_name, arguments=arguments
        )
    return message.content


class TestTracedToolCall:
    @pytest.mark.asyncio
    async def test_records_arguments_result_and_server(self, exporter: InMemorySpanExporter):
        content = await _call("echo", {"text": "hi"})

        [span] = _tool_spans(exporter)
        assert content == "echo: hi"
        assert span.attributes[SpanAttributes.TOOL_NAME] == "echo"
        assert json.loads(span.attributes[SpanAttributes.INPUT_VALUE]) == {"text": "hi"}
        assert span.attributes[SpanAttributes.OUTPUT_VALUE] == "echo: hi"
        assert span.attributes["mcp.server.name"] == "echo-server"
        assert span.attributes["mcp.auth_mode"] == "api_key"
        assert span.attributes["mcp.method.name"] == "tools/call"
        assert span.status.status_code == StatusCode.OK

    @pytest.mark.asyncio
    async def test_never_records_the_connection_credentials(self, exporter: InMemorySpanExporter):
        await _call("echo", {"text": "hi"})

        recorded = json.dumps([dict(span.attributes) for span in exporter.get_finished_spans()])
        assert "sk-secret" not in recorded

    @pytest.mark.asyncio
    async def test_fastmcp_request_span_nests_under_the_tool_span(self, exporter: InMemorySpanExporter):
        await _call("echo", {"text": "hi"})

        [tool_span] = _tool_spans(exporter)
        request_spans = [
            span for span in exporter.get_finished_spans() if span.attributes.get("mcp.method.name") == "tools/call"
        ]
        children = [span for span in request_spans if span is not tool_span]
        assert children, "FastMCP should trace the protocol request"
        assert all(span.parent.span_id == tool_span.context.span_id for span in children)


class TestRefusedCallGoesBackToTheModel:
    @pytest.mark.asyncio
    async def test_failing_tool_returns_an_error_result(self, exporter: InMemorySpanExporter):
        content = await _call("fail", {})

        [span] = _tool_spans(exporter)
        assert content == "Error: the backend is down"
        assert span.status.status_code == StatusCode.ERROR

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_an_error_result(self, exporter: InMemorySpanExporter):
        content = await _call("no_such_tool", {})

        [span] = _tool_spans(exporter)
        assert content.startswith("Error: ")
        assert span.status.status_code == StatusCode.ERROR


class TestTracedResourceRead:
    @pytest.mark.asyncio
    async def test_resource_read_is_traced_as_a_tool(self, exporter: InMemorySpanExporter):
        content = await _call(READ_MCP_RESOURCE_TOOL_NAME, {"uri": "doc://readme"})

        [span] = _tool_spans(exporter)
        assert content == "read me first"
        assert span.attributes["mcp.method.name"] == "resources/read"
        assert span.attributes[SpanAttributes.OUTPUT_VALUE] == "read me first"

    @pytest.mark.asyncio
    async def test_unknown_resource_returns_an_error_result(self, exporter: InMemorySpanExporter):
        content = await _call(READ_MCP_RESOURCE_TOOL_NAME, {"uri": "doc://missing"})

        [span] = _tool_spans(exporter)
        assert content.startswith("Error: ")
        assert span.status.status_code == StatusCode.ERROR
