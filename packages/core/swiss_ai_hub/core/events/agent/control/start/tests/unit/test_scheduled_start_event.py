import json
from datetime import UTC, datetime

import pytest

from swiss_ai_hub.core.events.agent.control.start.scheduled_start_event import ScheduledStartEvent
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.base_event import BaseEvent

_OCCURRENCE = datetime(2026, 8, 11, 12, tzinfo=UTC)


class TestScheduledStartEvent:
    def test_starts_a_run(self):
        assert issubclass(ScheduledStartEvent, StartEvent)
        assert ScheduledStartEvent(scheduled_for=_OCCURRENCE).is_start_event

    def test_is_not_a_user_message(self):
        """Were it one, every schedulable agent would also be reported conversational and appear in chat."""
        assert not issubclass(ScheduledStartEvent, UserMessageEvent)

    def test_carries_no_user_by_default(self):
        """Scheduled runs are system runs — the absence of a user is the contract, not an oversight."""
        assert ScheduledStartEvent(scheduled_for=_OCCURRENCE).user is None

    def test_carries_the_occurrence_it_fired_for(self):
        assert ScheduledStartEvent(scheduled_for=_OCCURRENCE).scheduled_for == _OCCURRENCE

    def test_requires_the_occurrence(self):
        with pytest.raises(ValueError, match="scheduled_for"):
            ScheduledStartEvent()

    def test_polymorphic_round_trip(self):
        event = ScheduledStartEvent(scheduled_for=_OCCURRENCE)
        restored = BaseEvent.deserialize_event(event.model_dump())

        assert isinstance(restored, ScheduledStartEvent)
        assert restored.scheduled_for == _OCCURRENCE
        assert restored.user is None

    def test_context_dict_is_json_serializable(self):
        """The dispatcher writes every context value into RunContext, which serializes with json.dumps.

        Without this, `scheduled_for` being a `datetime` raised TypeError inside the store on every
        single run — the scheduler fired correctly, the agent fetched its config, and then the run died
        before any step executed. Nothing else covered the path from a start event into RunContext, so
        the whole feature shipped green and non-functional.
        """
        context = ScheduledStartEvent(scheduled_for=_OCCURRENCE).to_context_dict()

        json.dumps(context)
        assert isinstance(context["scheduled_for"], str)

    def test_occurrence_survives_the_context_round_trip(self):
        """RunContext reads back with json.loads, so the value must still identify the occurrence."""
        context = json.loads(json.dumps(ScheduledStartEvent(scheduled_for=_OCCURRENCE).to_context_dict()))

        assert datetime.fromisoformat(context["scheduled_for"]) == _OCCURRENCE

    @pytest.mark.parametrize("locale", ["de", "en", "fr", "it"])
    def test_display_name_and_description_resolve(self, locale: str):
        assert ScheduledStartEvent._display_name.in_locale(locale)
        assert ScheduledStartEvent._display_description.in_locale(locale)
