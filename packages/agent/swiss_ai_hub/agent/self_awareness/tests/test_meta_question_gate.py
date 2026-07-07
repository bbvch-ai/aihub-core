"""Infra-free guards for the meta-question gate predicate.

The per-agent wiring tests were removed together with the agents' meta-question steps; the gate
predicate itself remains shared self-awareness infrastructure and is still validated here.
"""

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import NotAMetaQuestionEvent, UserMessageEvent
from swiss_ai_hub.core.testing.auth_utils import fake_user

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
