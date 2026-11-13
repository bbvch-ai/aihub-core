"""NATS headers carry X-AIHub-* values, among them a user's access token, so the propagator's debug logs show only the
trace context."""

import logging

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from swiss_ai_hub.core.tracing.nats_trace_context_propagator import NATSTraceContextPropagator

USER_TOKEN = "eyJ.user-access-token.signature"
TRACEPARENT = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"


@pytest.fixture
def debug_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    caplog.set_level(logging.DEBUG, logger="swiss_ai_hub.core.tracing.nats_trace_context_propagator")
    return caplog


def test_activating_a_trace_context_logs_it_without_the_user_token(debug_logs: pytest.LogCaptureFixture) -> None:
    NATSTraceContextPropagator.extract_and_activate_trace_context(
        {"traceparent": TRACEPARENT, "x-aihub-user-token": USER_TOKEN}
    )

    assert TRACEPARENT in debug_logs.text
    assert USER_TOKEN not in debug_logs.text


def test_injecting_a_trace_context_logs_it_without_other_headers(debug_logs: pytest.LogCaptureFixture) -> None:
    tracer = TracerProvider().get_tracer(__name__)
    with trace.use_span(tracer.start_span("publish"), end_on_exit=True):
        NATSTraceContextPropagator.inject_trace_context({"X-AIHub-User-Token": USER_TOKEN})

    assert "traceparent" in debug_logs.text
    assert USER_TOKEN not in debug_logs.text
