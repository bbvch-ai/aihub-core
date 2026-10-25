import mongoengine
import pytest
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity
from swiss_ai_hub.core.routes.chat.chat_service import ChatService
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

AGENT_CLASS = "TestAgent"
AGENT_ID = "test-agent"


def _raise_does_not_exist(cls, thread_id: str) -> ThreadEntity:
    raise mongoengine.errors.DoesNotExist()


def test_a_client_cannot_start_a_chat_under_the_scheduled_run_thread_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """The scheduled-run thread id is derivable from the profile, so a client must not claim it first."""
    created: list[dict] = []
    monkeypatch.setattr(ThreadEntity, "get_thread_by_id", classmethod(_raise_does_not_exist))
    monkeypatch.setattr(ThreadEntity, "create_thread", classmethod(lambda cls, *a, **kw: created.append(kw)))
    scheduled_thread_id = ThreadEntity.scheduled_thread_id(AgentInstanceRef(agent_class=AGENT_CLASS, agent_id=AGENT_ID))

    with pytest.raises(HTTPException) as raised:
        ChatService._initialize_interaction(
            user=fake_user(),
            agent_class=AGENT_CLASS,
            agent_id=AGENT_ID,
            messages=[ChatMessage(role=MessageRole.USER, content="hello")],
            thread_id=scheduled_thread_id,
        )

    assert raised.value.status_code == 409
    assert created == []
