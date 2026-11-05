"""Unit tests for the web fetch capability's events (issue #1569).

The request and its result are protocol events, so both are displayed; the result is also a semantic event, which is
what puts every fetch into the agent's trace as a retrieval of the pages read.
"""

import json

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.agent.web_fetch.fetch_web_pages_event import FetchWebPagesEvent
from swiss_ai_hub.core.events.agent.web_fetch.web_fetch_failure import WebFetchFailure
from swiss_ai_hub.core.events.agent.web_fetch.web_fetch_failure_reason import WebFetchFailureReason
from swiss_ai_hub.core.events.agent.web_fetch.web_pages_fetched_event import WebPagesFetchedEvent
from swiss_ai_hub.core.events.base_event import BaseEvent
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.testing.auth_utils import fake_user

PAGE_URL = "https://example.com/article"


def _page_node() -> IngestedNode:
    return IngestedNode(
        id="page-1",
        document_id="page-1",
        content="# Article\n\nThe article's text.",
        source=PAGE_URL,
        source_origin=PAGE_URL,
        namespace="web",
        document_title="Article",
        created_at="2026-10-15T00:00:00Z",
        updated_at="2026-10-15T00:00:00Z",
        inserted_at="2026-10-15T00:00:00Z",
    )


def _fetched() -> WebPagesFetchedEvent:
    return WebPagesFetchedEvent(
        block=[ChatMessage(role=MessageRole.SYSTEM, content="<page>The article's text.</page>")],
        grounding_nodes=[_page_node()],
        failures=[WebFetchFailure(url="https://example.com/gone", reason=WebFetchFailureReason.NOT_FOUND)],
        tool_call_id="call-1",
    )


def test_request_and_result_are_protocol_events():
    """The event history lists display events only, so a call nobody can see would vanish from a run's history."""
    request = FetchWebPagesEvent(urls=[PAGE_URL])
    result = _fetched()
    assert request.is_control_event
    assert request.is_display_event
    assert result.is_control_event
    assert result.is_display_event
    assert result.is_semantic_event


def test_result_round_trips_with_its_pages_failures_and_block():
    restored = BaseEvent.deserialize_event(_fetched().model_dump())

    assert isinstance(restored, WebPagesFetchedEvent)
    assert restored.grounding_nodes[0].source_origin == PAGE_URL
    assert restored.grounding_nodes[0].document_title == "Article"
    assert restored.failures == [
        WebFetchFailure(url="https://example.com/gone", reason=WebFetchFailureReason.NOT_FOUND)
    ]
    assert restored.block[0].content == "<page>The article's text.</page>"
    assert restored.tool_call_id == "call-1"


def test_trace_shows_the_fetch_as_a_retrieval_of_the_pages_read():
    attributes = _fetched().to_semantic_convention()

    assert attributes[SpanAttributes.OPENINFERENCE_SPAN_KIND] == OpenInferenceSpanKindValues.RETRIEVER.value
    assert attributes[f"{SpanAttributes.RETRIEVAL_DOCUMENTS}.0.document.content"] == "# Article\n\nThe article's text."
    assert json.loads(attributes[SpanAttributes.METADATA]) == {
        "failures": [{"url": "https://example.com/gone", "reason": "not_found"}]
    }


def test_trace_of_a_fetch_without_failures_carries_no_failure_metadata():
    attributes = WebPagesFetchedEvent(grounding_nodes=[_page_node()]).to_semantic_convention()

    assert SpanAttributes.METADATA not in attributes


def test_message_keeps_a_malformed_web_reference_for_the_agent_to_report():
    """Validating the links here would reject the whole message; the agent reports a bad one instead."""
    event = UserMessageEvent(user=fake_user(), web_references=["https://example.com/a", "not a url"])

    restored = BaseEvent.deserialize_event(event.model_dump())

    assert restored.web_references == ["https://example.com/a", "not a url"]


def test_message_from_before_web_references_still_deserializes():
    """Events already in JetStream at deploy time carry no such field."""
    payload = UserMessageEvent(user=fake_user()).model_dump()
    payload.pop("web_references")

    restored = BaseEvent.deserialize_event(payload)

    assert restored.web_references == []
