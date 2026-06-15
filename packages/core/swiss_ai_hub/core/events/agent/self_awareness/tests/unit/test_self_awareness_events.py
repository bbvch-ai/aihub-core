from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.agent.self_awareness.meta_question_detected_event import MetaQuestionDetectedEvent
from swiss_ai_hub.core.events.agent.self_awareness.not_a_meta_question_event import NotAMetaQuestionEvent
from swiss_ai_hub.core.events.base_event import BaseEvent


class TestMetaQuestionDetectedEvent:
    def test_carries_query_category_and_reasoning(self):
        event = MetaQuestionDetectedEvent(
            user_query="what can you do?", category="capabilities", reasoning="asks about abilities"
        )
        assert event.user_query == "what can you do?"
        assert event.category == "capabilities"
        assert event.reasoning == "asks about abilities"

    def test_is_a_display_event_so_the_ui_can_render_it(self):
        assert issubclass(MetaQuestionDetectedEvent, DisplayEvent)

    def test_display_name_resolves(self):
        event = MetaQuestionDetectedEvent(user_query="q", category="identity", reasoning="r")
        assert event._display_name.in_locale("en")

    def test_polymorphic_round_trip(self):
        event = MetaQuestionDetectedEvent(user_query="q", category="behavior", reasoning="r")
        restored = BaseEvent.deserialize_event(event.model_dump())
        assert isinstance(restored, MetaQuestionDetectedEvent)
        assert restored.category == "behavior"


class TestNotAMetaQuestionEvent:
    def test_carries_reasoning(self):
        assert NotAMetaQuestionEvent(reasoning="normal task").reasoning == "normal task"

    def test_is_control_only_not_displayed(self):
        """The gate signal is internal — it must not surface in the UI timeline."""
        assert issubclass(NotAMetaQuestionEvent, ControlEvent)
        assert not issubclass(NotAMetaQuestionEvent, DisplayEvent)
