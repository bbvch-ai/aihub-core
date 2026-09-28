"""Infra-free guards for the meta-question gating: the pure gate predicate and the workflow wiring."""

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ContextualizeConversationEvent,
    ConversationContextualizedEvent,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    RetrieveOrganizationMemoryEvent,
    RetrieverEvent,
    RetrieveUserMemoryEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.self_awareness.meta_question_gate import check_passed_meta_question_gate


def _user_message() -> UserMessageEvent:
    return UserMessageEvent(
        messages=[ChatMessage(content="what can you do?", role=MessageRole.USER)],
        user=fake_user(),
        locale="en",
    )


def test_gate_blocks_chat_entry_until_cleared():
    """A chat (UserMessageEvent) entry stays blocked until detection emits the clear."""
    assert check_passed_meta_question_gate(_user_message(), clear=None) is False
    assert check_passed_meta_question_gate(_user_message(), clear=NotAMetaQuestionEvent(reasoning="ok")) is True


def test_gate_lets_programmatic_starts_through():
    """A non-chat (programmatic) start bypasses detection entirely."""
    programmatic_start = object()  # stand-in for RAGStartEvent — anything that is not a UserMessageEvent
    assert check_passed_meta_question_gate(programmatic_start, clear=None) is True


def test_detection_is_the_only_gate_between_the_call_and_the_query():
    """
    `derive_query_step` is the only step waiting on NotAMetaQuestionEvent, and it is the only producer of the
    contextualized turn every other step hangs off, so nothing that does work for the turn can start before
    inspection clears the message. The blueprint's entry step runs ungated on purpose: it only limits the
    history and makes the call.
    """
    gated = {s.__name__ for s in RAGAgent.get_steps_waiting_for_event(NotAMetaQuestionEvent)}
    assert gated == {"derive_query_step"}


def test_memory_and_retrieval_hang_off_the_contextualized_turn():
    """Recall and retrieval consume the call's result, which only exists past the gate. A refactor that
    re-anchors them on the start event alone must restore an explicit gate."""
    on_turn = {s.__name__ for s in RAGAgent.get_steps_waiting_for_event(ConversationContextualizedEvent)}
    assert {"recall_memory_step", "few_shot_guard_step", "retrieve_step", "assemble_prompt_step"} <= on_turn


def test_inspection_reads_the_call_never_a_start_event():
    """Inspection consumes the contextualize request, so a programmatic start (no user query on it) is cleared
    without a detection call and a chat message is inspected — the blueprint decides by what it hands over."""
    inspect_inputs = next(s._input_events for s in RAGAgent.get_steps() if s.__name__ == "inspect_message_step")
    assert inspect_inputs == {ContextualizeConversationEvent}


def test_answer_step_terminates_and_skips_retrieval():
    """answer_meta_question_step is wired off MetaQuestionDetectedEvent and produces no retrieval.

    generate_meta_question_title_step also waits on this event — deliberately, so the dispatcher runs
    the title generation concurrently with the meta answer instead of serializing it behind the answer.
    """
    answer_steps = {s.__name__ for s in RAGAgent.get_steps_waiting_for_event(MetaQuestionDetectedEvent)}
    assert answer_steps == {"answer_meta_question_step", "generate_meta_question_title_step"}

    retrieval_events = {RetrieverEvent, RetrieveUserMemoryEvent, RetrieveOrganizationMemoryEvent}
    answer_step = next(s for s in RAGAgent.get_steps() if s.__name__ == "answer_meta_question_step")
    assert not retrieval_events.intersection(answer_step._output_events)
