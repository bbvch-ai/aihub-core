"""Infra-free guards for the meta-question gating: the pure gate predicate and the workflow wiring."""

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    ConversationQueryEvent,
    LimitChatHistoryEvent,
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


def test_detection_is_the_only_step_firing_on_a_raw_chat_message_among_entry_steps():
    """
    On the conversational spine the gate sits on `derive_query_step`, the first step past the entry point:
    it is the only step waiting on NotAMetaQuestionEvent, and everything that could do work for the turn —
    enrichers, retrieval, the answer — is downstream of it. Limiting the history runs ungated on purpose:
    it is cheap and side-effect free, and gating it would only delay detection's own input.
    """
    gated = {s.__name__ for s in RAGAgent.get_steps_waiting_for_event(NotAMetaQuestionEvent)}
    assert gated == {"derive_query_step"}


def test_memory_steps_are_gated_transitively_through_the_query():
    """
    The memory enrichers hang off the spine's query event, which only exists past the gate, and the join
    that feeds the answer pipeline waits for their blocks. A refactor that re-anchors them on the start
    event alone must restore an explicit gate.
    """
    query_gated = {s.__name__ for s in RAGAgent.get_steps_waiting_for_event(ConversationQueryEvent)}
    assert {"retrieve_user_memory_step", "retrieve_organization_memory_step"} <= query_gated
    limit_gated = {s.__name__ for s in RAGAgent.get_steps_waiting_for_event(LimitChatHistoryEvent)}
    assert "assemble_context_step" in limit_gated


def test_detect_step_does_not_run_on_programmatic_start():
    """detect_meta_question_step consumes only UserMessageEvent, so RAGStartEvent skips detection."""
    detect_inputs = next(s._input_events for s in RAGAgent.get_steps() if s.__name__ == "detect_meta_question_step")
    assert UserMessageEvent in detect_inputs
    from swiss_ai_hub.core.events.agent import RAGStartEvent

    assert RAGStartEvent not in detect_inputs


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
