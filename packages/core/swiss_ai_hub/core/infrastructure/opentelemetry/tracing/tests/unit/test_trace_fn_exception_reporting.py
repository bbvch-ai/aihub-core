from unittest.mock import patch

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import SmartTracer

pytestmark = pytest.mark.unit

_TRACE_FN_MODULE = "swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn"


def _local_tracer(exporter: InMemorySpanExporter) -> SmartTracer:
    """A provider of its own, so the test neither depends on nor installs the global one."""
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return SmartTracer(provider.get_tracer("test"))


class TestFailingTracedCallIsReportedOnce:
    """The SDK records the exception and sets the ERROR status itself when the wrapper re-raises
    out of the span context, so recording it in the decorator as well double-counted every
    exception in the observability backend."""

    @pytest.mark.asyncio
    async def test_async_failure_records_a_single_exception_event(self):
        exporter = InMemorySpanExporter()

        @trace_fn
        async def failing_call() -> None:
            raise ValueError("upstream rejected the model name")

        with patch(f"{_TRACE_FN_MODULE}.get_tracer", return_value=_local_tracer(exporter)):
            with pytest.raises(ValueError):
                await failing_call()

        span = exporter.get_finished_spans()[0]
        assert [event.name for event in span.events] == ["exception"]
        assert span.status.status_code is StatusCode.ERROR
        assert span.attributes["operation.success"] is False
        assert span.attributes["error.type"] == "ValueError"

    def test_sync_failure_records_a_single_exception_event(self):
        exporter = InMemorySpanExporter()

        @trace_fn
        def failing_call() -> None:
            raise ValueError("upstream rejected the model name")

        with patch(f"{_TRACE_FN_MODULE}.get_tracer", return_value=_local_tracer(exporter)):
            with pytest.raises(ValueError):
                failing_call()

        span = exporter.get_finished_spans()[0]
        assert [event.name for event in span.events] == ["exception"]
        assert span.status.status_code is StatusCode.ERROR

    def test_successful_call_leaves_no_exception_event(self):
        exporter = InMemorySpanExporter()

        @trace_fn
        def working_call() -> str:
            return "done"

        with patch(f"{_TRACE_FN_MODULE}.get_tracer", return_value=_local_tracer(exporter)):
            assert working_call() == "done"

        span = exporter.get_finished_spans()[0]
        assert span.events == ()
        assert span.attributes["operation.success"] is True
