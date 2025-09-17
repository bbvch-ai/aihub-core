from collections.abc import Generator, Sequence
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.context import get_value
from opentelemetry.trace import INVALID_SPAN_CONTEXT, Link, NonRecordingSpan, Span, SpanKind, Tracer, TracerProvider
from opentelemetry.util.types import Attributes


class SmartTracer(Tracer):
    """A Tracer wrapper that respects suppress_instrumentation context."""

    def __init__(self, tracer: Tracer):
        """Wrap an existing tracer."""
        self._tracer = tracer
        self._instrumenting_module_name = getattr(tracer, "_instrumenting_module_name", "")
        self._instrumenting_library_version = getattr(tracer, "_instrumenting_library_version", "")

    def start_span(
        self,
        name: str,
        context: trace.Context | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes | None = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ) -> Span:
        """Start a new span, or return a no-op span if suppressed."""
        if get_value("suppress_instrumentation"):
            return NonRecordingSpan(INVALID_SPAN_CONTEXT)

        return self._tracer.start_span(
            name=name,
            context=context,
            kind=kind,
            attributes=attributes,
            links=links,
            start_time=start_time,
            record_exception=record_exception,
            set_status_on_exception=set_status_on_exception,
        )

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        context: trace.Context | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes | None = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
        end_on_exit: bool = True,
    ) -> Generator[Span]:
        """Start a span as the current span, or yield a no-op span if suppressed."""
        if get_value("suppress_instrumentation"):
            yield NonRecordingSpan(INVALID_SPAN_CONTEXT)
        else:
            with self._tracer.start_as_current_span(
                name=name,
                context=context,
                kind=kind,
                attributes=attributes,
                links=links,
                start_time=start_time,
                record_exception=record_exception,
                set_status_on_exception=set_status_on_exception,
                end_on_exit=end_on_exit,
            ) as span:
                yield span


class SmartTracerProvider(TracerProvider):
    """A TracerProvider that returns SmartTracers."""

    def __init__(self, provider: TracerProvider | None = None):
        """Wrap an existing provider or use the global one."""
        self._provider = provider or trace.get_tracer_provider()

    def get_tracer(
        self,
        instrumenting_module_name: str,
        instrumenting_library_version: str | None = None,
        schema_url: str | None = None,
        attributes: Attributes | None = None,
    ) -> Tracer:
        """Get a SmartTracer that wraps the real tracer."""
        real_tracer = self._provider.get_tracer(
            instrumenting_module_name, instrumenting_library_version, schema_url, attributes
        )
        return SmartTracer(real_tracer)


_smart_provider = SmartTracerProvider()


def get_tracer(
    instrumenting_module_name: str,
    instrumenting_library_version: str | None = None,
    schema_url: str | None = None,
    attributes: Attributes | None = None,
) -> SmartTracer:
    """
    Drop-in replacement for trace.get_tracer() that returns a SmartTracer.

    This function has the same signature as opentelemetry.trace.get_tracer()
    for maximum compatibility.
    """
    return _smart_provider.get_tracer(instrumenting_module_name, instrumenting_library_version, schema_url, attributes)
