from aihub_mcp.tracing.MCPTracer import MCPTracer


class TestMCPTracer:
    """Tests for MCPTracer class."""

    def test_tracer_creates_span(self) -> None:
        """Test that tracer creates spans."""
        tracer = MCPTracer(service_name="test")
        span = tracer.start_tool_span("test_tool", "TestAgent")
        assert span is not None
        tracer.end_span(span, success=True)

    def test_add_event_null_span_no_error(self) -> None:
        """Test that add_event doesn't error with None span."""
        tracer = MCPTracer(service_name="test")
        # Should not raise even with None span
        tracer.add_event(None, "test_event", {"key": "value"})

    def test_add_event_with_span(self) -> None:
        """Test adding events to a span."""
        tracer = MCPTracer(service_name="test")
        span = tracer.start_tool_span("test_tool", "TestAgent")

        # Should not raise
        tracer.add_event(span, "processing", {"step": 1})
        tracer.add_event(span, "completed", {"result": "success"})

        tracer.end_span(span, success=True)

    def test_end_span_with_error(self) -> None:
        """Test ending a span with an error."""
        tracer = MCPTracer(service_name="test")
        span = tracer.start_tool_span("failing_tool", "TestAgent")

        # Should not raise
        tracer.end_span(span, success=False, error_message="Something went wrong")

    def test_end_span_null_span_no_error(self) -> None:
        """Test that end_span doesn't error with None span."""
        tracer = MCPTracer(service_name="test")
        # Should not raise even with None span
        tracer.end_span(None, success=True)

    def test_span_attributes(self) -> None:
        """Test that span includes custom attributes."""
        tracer = MCPTracer(service_name="test")
        span = tracer.start_tool_span(
            tool_name="my_tool",
            agent_class="MyAgent",
            attributes={"custom.attr": "value"},
        )
        assert span is not None
        tracer.end_span(span, success=True)

    def test_nested_spans(self) -> None:
        """Test that nested spans work correctly."""
        tracer = MCPTracer(service_name="test")

        outer_span = tracer.start_tool_span("outer_tool", "Agent1")
        inner_span = tracer.start_tool_span("inner_tool", "Agent2")

        tracer.end_span(inner_span, success=True)
        tracer.end_span(outer_span, success=True)

    def test_tracer_service_name(self) -> None:
        """Test that tracer stores service name."""
        tracer = MCPTracer(service_name="aihub_mcp")
        assert tracer._service_name == "aihub_mcp"
