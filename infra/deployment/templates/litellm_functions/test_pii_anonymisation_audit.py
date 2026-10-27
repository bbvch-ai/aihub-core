"""Unit tests for pii_anonymisation_audit.py: the span an admin finds in Langfuse for every anonymised call.

NOT part of a CI `make test` scope (see test_pii_anonymisation_guardrail.py). Run with the packages the LiteLLM image
ships:

    uv run --with "litellm==1.106.2" --with opentelemetry-exporter-otlp-proto-grpc \
        pytest infra/deployment/templates/litellm_functions/test_pii_anonymisation_audit.py
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

sys.path.insert(0, str(Path(__file__).parent))
from pii_anonymisation_audit import AnonymisationAudit
from test_pii_anonymisation_guardrail import make_guardrail

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
TRACEPARENT = f"00-{TRACE_ID}-00f067aa0ba902b7-01"
TOKENS = {"<PERSON_1>": "Reto Wyss", "<NATIONAL_ID_2>": "756.1234.5678.97", "<PERSON_3>": "Anna Muster"}
METADATA = "langfuse.observation.metadata."
MASKED = [{"role": "user", "content": "Patient <PERSON_1>, AHV <NATIONAL_ID_2>, Kopie an <PERSON_3>"}]


@pytest.fixture
def spans() -> InMemorySpanExporter:
    return InMemorySpanExporter()


def _audit(spans: InMemorySpanExporter) -> AnonymisationAudit:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(spans))
    return AnonymisationAudit(tracer=provider.get_tracer("test"))


def _data(headers: dict | None = None, messages: list | None = None) -> dict:
    return {"model": "text-generation/gemma-4-31B-it", "messages": messages or MASKED,
            "proxy_server_request": {"headers": headers or {}}}


def test_should_put_the_span_into_the_callers_trace_with_what_the_provider_received(spans) -> None:
    _audit(spans).record(_data({"traceparent": TRACEPARENT}), TOKENS, "model outside the deployment", 0)

    [span] = spans.get_finished_spans()
    assert format(span.context.trace_id, "032x") == TRACE_ID
    assert span.name == "pii-anonymisation"
    assert span.attributes["openinference.span.kind"] == "GUARDRAIL"
    assert json.loads(span.attributes["input.value"]) == MASKED
    assert "Reto Wyss" not in span.attributes["input.value"]


def test_should_say_how_many_values_of_which_type_were_replaced_and_why(spans) -> None:
    _audit(spans).record(_data({"Traceparent": TRACEPARENT}), TOKENS, "requested by the call", 0)

    [span] = spans.get_finished_spans()
    assert span.attributes["output.value"] == "3 values replaced before the call: NATIONAL_ID 1, PERSON 2"
    metadata = {key.removeprefix(METADATA): value for key, value in span.attributes.items() if key.startswith(METADATA)}
    assert metadata == {"model": "text-generation/gemma-4-31B-it", "reason": "requested by the call",
                        "values_replaced": 3, "by_type": '{"NATIONAL_ID": 1, "PERSON": 2}'}


def test_should_record_counts_only_for_a_call_outside_a_run(spans) -> None:
    _audit(spans).record(_data(), TOKENS, "model outside the deployment", 0)

    [span] = spans.get_finished_spans()
    assert span.parent is None
    assert "input.value" not in span.attributes
    assert span.attributes["output.value"].startswith("3 values replaced")


def test_should_mark_a_refused_call_as_an_error_without_its_text(spans) -> None:
    _audit(spans).record(_data({"traceparent": TRACEPARENT}), {}, "model outside the deployment", 0,
                         error="PII anonymisation is unavailable, so the request was not sent: ConnectError")

    [span] = spans.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
    assert "input.value" not in span.attributes
    assert span.attributes["output.value"].startswith("Refused, nothing was sent")


def test_should_leave_images_out_and_cut_a_long_prompt() -> None:
    messages = [{"role": "user", "content": [{"type": "text", "text": "x" * 30_000},
                                             {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]}]

    sent = AnonymisationAudit.sent_messages(messages)

    assert "base64" not in sent
    assert len(sent) == 20_000


def test_should_record_nothing_without_a_collector(monkeypatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

    audit = AnonymisationAudit()

    assert audit.tracer is None
    audit.record(_data({"traceparent": TRACEPARENT}), TOKENS, "model outside the deployment", 0)


def test_should_be_recorded_by_the_guardrail_with_the_masked_request(spans) -> None:
    guardrail = make_guardrail()
    guardrail.audit = _audit(spans)
    data = {"model": "external-model", "litellm_call_id": "call-9",
            "messages": [{"role": "user", "content": "Patient Reto Wyss, AHV 756.1234.5678.97"}],
            "proxy_server_request": {"headers": {"traceparent": TRACEPARENT}}}

    asyncio.run(guardrail.async_pre_call_hook(None, None, data, "acompletion"))

    [span] = spans.get_finished_spans()
    assert "Reto Wyss" not in span.attributes["input.value"]
    assert "<PERSON_1>" in span.attributes["input.value"]
    assert span.attributes[f"{METADATA}reason"] == "model outside the deployment"
