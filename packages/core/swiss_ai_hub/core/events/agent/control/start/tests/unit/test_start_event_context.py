import json
from datetime import UTC, datetime
from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent


class _StartEventWithRichTypes(StartEvent):
    """A start event whose fields JSON cannot represent natively.

    Declared here rather than reusing a production event so the guard keeps working as the real events
    change — it protects the mechanism, not one event's current field list.
    """

    occurrence: Annotated[datetime, Field(description="A timezone-aware instant.")]
    ratio: Annotated[float, Field(description="A plain float, to confirm ordinary types are untouched.")] = 0.5


class TestToContextDict:
    """`RunContext.set` serializes with `json.dumps` and `get` reads back with `json.loads`, so a
    context dict that is not JSON-serializable kills the run before any step executes — and does it
    inside the store, far from the event that caused it."""

    def test_rich_types_are_serializable(self):
        event = _StartEventWithRichTypes(occurrence=datetime(2026, 8, 18, 9, 10, tzinfo=UTC))

        json.dumps(event.to_context_dict())

    def test_values_match_what_the_store_reads_back(self):
        """Dumping in JSON mode is what makes the write and read halves agree on types."""
        event = _StartEventWithRichTypes(occurrence=datetime(2026, 8, 18, 9, 10, tzinfo=UTC))

        context = event.to_context_dict()
        assert json.loads(json.dumps(context)) == context

    def test_framework_fields_are_excluded(self):
        event = _StartEventWithRichTypes(occurrence=datetime(2026, 8, 18, 9, 10, tzinfo=UTC))

        context = event.to_context_dict()
        assert "event_id" not in context
        assert "created_at" not in context
        assert context["ratio"] == 0.5
