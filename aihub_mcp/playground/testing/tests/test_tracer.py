from aihub_mcp.tracing.MCPTracer import MCPTracer


class TestMCPTracer:
    """Tests for MCPTracer class."""

    def test_tracer_creates_span(self) -> None:
        """Test that tracer creates spans."""
        tracer = MCPTracer()
        span = tracer.start_tool_span("test_tool", "TestAgent")
        assert span is not None
        tracer.end_span(span, success=True)

    def test_add_event_with_span(self) -> None:
        """Test adding events to a span."""
        tracer = MCPTracer()
        span = tracer.start_tool_span("test_tool", "TestAgent")

        tracer.add_event(span, "processing", {"step": 1})
        tracer.add_event(span, "completed", {"result": "success"})

        tracer.end_span(span, success=True)

    def test_end_span_with_error(self) -> None:
        """Test ending a span with an error."""
        tracer = MCPTracer()
        span = tracer.start_tool_span("failing_tool", "TestAgent")

        tracer.end_span(span, success=False, error_message="Something went wrong")

    def test_span_attributes(self) -> None:
        """Test that span includes custom attributes."""
        tracer = MCPTracer()
        span = tracer.start_tool_span(
            tool_name="my_tool",
            agent_class="MyAgent",
            attributes={"custom.attr": "value"},
        )
        assert span is not None
        tracer.end_span(span, success=True)

    def test_nested_spans(self) -> None:
        """Test that nested spans work correctly."""
        tracer = MCPTracer()

        outer_span = tracer.start_tool_span("outer_tool", "Agent1")
        inner_span = tracer.start_tool_span("inner_tool", "Agent2")

        tracer.end_span(inner_span, success=True)
        tracer.end_span(outer_span, success=True)

    def test_tracer_name(self) -> None:
        """Test that tracer has correct name."""
        assert MCPTracer.TRACER_NAME == "aihub_mcp"
