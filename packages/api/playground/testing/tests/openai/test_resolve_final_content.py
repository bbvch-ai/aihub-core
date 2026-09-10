from types import SimpleNamespace

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService


def _assistant_stop_event(content: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        is_hitl_request_event=False,
        is_exception_event=False,
        output_messages=[ChatMessage(role=MessageRole.ASSISTANT, content=content)],
    )


def test_resolve_final_content_emits_full_answer_when_nothing_streamed():
    stop_event = _assistant_stop_event("the whole answer")

    assert OpenaiService._resolve_final_content(stop_event, streamed="") == "the whole answer"


def test_resolve_final_content_emits_only_remainder_on_partial_stream():
    stop_event = _assistant_stop_event("the whole answer")

    assert OpenaiService._resolve_final_content(stop_event, streamed="the whole ") == "answer"


def test_resolve_final_content_emits_nothing_when_fully_streamed():
    stop_event = _assistant_stop_event("the whole answer")

    assert OpenaiService._resolve_final_content(stop_event, streamed="the whole answer") == ""


def test_resolve_final_content_keeps_streamed_when_value_diverges():
    """When what streamed is not a prefix of the answer, stay conservative and emit nothing extra."""
    stop_event = _assistant_stop_event("the whole answer")

    assert OpenaiService._resolve_final_content(stop_event, streamed="something else") == ""


def test_resolve_final_content_handles_none_message_content():
    stop_event = _assistant_stop_event(None)

    assert OpenaiService._resolve_final_content(stop_event, streamed="") == ""
