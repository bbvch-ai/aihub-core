"""OpenTelemetry record of every anonymised call, so an admin can see in Langfuse what a provider received.

The Hub's own traces are written by the agents before their calls reach the gateway, so they show the original text and
say nothing about anonymisation. This adds one span per call the guardrail handled: in the caller's trace when the
request carries a `traceparent` (agents send one with every call), holding the messages as the provider received them;
in a trace of its own, with counts only, when it does not (plain chats, whose text Langfuse does not store otherwise).
The OpenInference GUARDRAIL kind is what lets the collector forward it to Langfuse.

Bind-mounted next to pii_anonymisation_guardrail.py, so like it it depends only on the stdlib and what the LiteLLM image
ships (OpenTelemetry for LiteLLM's own `otel` callback). Spans go to OTEL_EXPORTER_OTLP_ENDPOINT; without it, or
without OpenTelemetry, nothing is recorded.
"""

import json
import os
from collections import Counter
from typing import Any

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
except ImportError:
    TracerProvider = None

SPAN_NAME = "pii-anonymisation"
# The span holds what the provider received; a long prompt is cut so one call cannot bloat the trace.
MAX_INPUT_CHARS = 20_000
METADATA_PREFIX = "langfuse.observation.metadata."


class AnonymisationAudit:
    """Writes the `pii-anonymisation` span of one call: what was replaced, why, and what the provider received."""

    def __init__(self, tracer: Any | None = None) -> None:
        self.tracer = tracer if tracer is not None else self._default_tracer()

    @staticmethod
    def _default_tracer() -> Any | None:
        if TracerProvider is None or not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
            return None
        provider = TracerProvider(resource=Resource.create({"service.name": "litellm-pii-anonymisation"}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        return provider.get_tracer(__name__)

    @staticmethod
    def sent_messages(messages: list[dict]) -> str:
        """The text parts of the messages as sent, without images, cut to MAX_INPUT_CHARS."""
        sent = []
        for message in messages:
            content = message.get("content")
            if isinstance(content, list):
                content = "\n".join(p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text")
            sent.append({"role": message.get("role"), "content": content})
        return json.dumps(sent, ensure_ascii=False)[:MAX_INPUT_CHARS]

    @staticmethod
    def summary(tokens: dict[str, str], error: str | None) -> str:
        if error:
            return f"Refused, nothing was sent: {error}"
        counts = Counter(token[1:].rsplit("_", 1)[0] for token in tokens)
        listed = ", ".join(f"{entity} {count}" for entity, count in sorted(counts.items()))
        return f"{len(tokens)} values replaced before the call: {listed}" if tokens else "No personal data detected"

    def record(self, data: dict, tokens: dict[str, str], reason: str, started_ns: int, error: str | None = None) -> None:
        if self.tracer is None:
            return
        headers = {key.lower(): value for key, value in ((data.get("proxy_server_request") or {}).get("headers") or {}).items()}
        in_run = "traceparent" in headers
        parent = TraceContextTextMapPropagator().extract(carrier=headers) if in_run else None
        counts = Counter(token[1:].rsplit("_", 1)[0] for token in tokens)
        span = self.tracer.start_span(SPAN_NAME, context=parent, start_time=started_ns)
        span.set_attribute("openinference.span.kind", "GUARDRAIL")
        # A refused call may be half masked, so its span keeps the reason and no text.
        if in_run and not error:
            span.set_attribute("input.value", self.sent_messages(data.get("messages") or []))
            span.set_attribute("input.mime_type", "application/json")
        span.set_attribute("output.value", self.summary(tokens, error))
        # Langfuse shows `langfuse.observation.metadata.*` attributes as the observation's metadata fields.
        metadata = {"model": data.get("model") or "", "reason": reason, "values_replaced": len(tokens),
                    "by_type": json.dumps(dict(sorted(counts.items())))}
        for key, value in metadata.items():
            span.set_attribute(f"{METADATA_PREFIX}{key}", value)
        if error:
            span.set_status(Status(StatusCode.ERROR, error))
        span.end()
