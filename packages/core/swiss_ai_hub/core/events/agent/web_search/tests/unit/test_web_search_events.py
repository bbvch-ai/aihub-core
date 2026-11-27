"""Unit tests for the web search capability's events (issue #1568).

Both are protocol events, so a run's history shows every search; the result is also a semantic event, which puts the
search into the agent's trace as a retrieval of the hits it handed the model.
"""

import json

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from swiss_ai_hub.core.events.agent.web_fetch.web_fetch_failure import WebFetchFailure
from swiss_ai_hub.core.events.agent.web_fetch.web_fetch_failure_reason import WebFetchFailureReason
from swiss_ai_hub.core.events.agent.web_search.search_web_event import SearchWebEvent
from swiss_ai_hub.core.events.agent.web_search.web_search_result import WebSearchResult
from swiss_ai_hub.core.events.agent.web_search.web_searched_event import WebSearchedEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode

HIT_URL = "https://example.com/release"


def _hit_node() -> IngestedNode:
    return IngestedNode(
        id="hit-1",
        document_id="hit-1",
        content="Version 2 was released today.",
        source=HIT_URL,
        source_origin=HIT_URL,
        namespace="web",
        document_title="Release notes",
        created_at="2026-11-25T00:00:00Z",
        updated_at="2026-11-25T00:00:00Z",
        inserted_at="2026-11-25T00:00:00Z",
    )


def _searched() -> WebSearchedEvent:
    return WebSearchedEvent(
        queries=["latest release"],
        results=[WebSearchResult(url=HIT_URL, title="Release notes", snippet="Version 2", engine="brave", read=True)],
        block=[ChatMessage(role=MessageRole.SYSTEM, content="<page>Version 2 was released today.</page>")],
        grounding_nodes=[_hit_node()],
        failures=[WebFetchFailure(url="https://example.com/slow", reason=WebFetchFailureReason.TIMEOUT)],
        unresponsive_engines=["duckduckgo: CAPTCHA"],
        tool_call_id="call-1",
    )


def test_request_and_result_are_protocol_events():
    request = SearchWebEvent(queries=["latest release"])
    result = _searched()
    assert request.is_control_event
    assert request.is_display_event
    assert result.is_control_event
    assert result.is_display_event
    assert result.is_semantic_event


def test_result_round_trips_with_its_hits_block_and_failures():
    restored = BaseEvent.deserialize_event(_searched().model_dump())

    assert isinstance(restored, WebSearchedEvent)
    assert restored.queries == ["latest release"]
    assert restored.results[0].url == HIT_URL
    assert restored.results[0].read
    assert restored.grounding_nodes[0].source_origin == HIT_URL
    assert restored.failures[0].reason == WebFetchFailureReason.TIMEOUT
    assert restored.tool_call_id == "call-1"


def test_trace_shows_the_search_as_a_retrieval_of_its_hits_for_its_queries():
    attributes = _searched().to_semantic_convention()

    assert attributes[SpanAttributes.OPENINFERENCE_SPAN_KIND] == OpenInferenceSpanKindValues.RETRIEVER.value
    assert attributes[SpanAttributes.INPUT_VALUE] == "latest release"
    assert attributes[f"{SpanAttributes.RETRIEVAL_DOCUMENTS}.0.document.content"] == "Version 2 was released today."
    assert json.loads(attributes[SpanAttributes.METADATA]) == {
        "failures": [{"url": "https://example.com/slow", "reason": "timeout"}],
        "unresponsive_engines": ["duckduckgo: CAPTCHA"],
    }


def test_trace_of_a_search_without_queries_or_failures_carries_neither():
    attributes = WebSearchedEvent().to_semantic_convention()

    assert SpanAttributes.INPUT_VALUE not in attributes
    assert SpanAttributes.METADATA not in attributes
