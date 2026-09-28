"""Memory operations use the turn's query, never the RAG-augmented prompt (#1753).

Chat clients running full-context RAG inline whole documents into the last user message. These tests pin
the structural guarantee on every RAG blueprint: the memory steps are wired downstream of the spine's query
event (search embeds the condensed question, not documents). The storage payload is pinned in
`capabilities/tests/test_memory_capability.py`.
"""

import pytest
from swiss_ai_hub.core.events.agent import ConversationQueryEvent, LimitChatHistoryEvent

from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent


def _steps_waiting_for(agent_class: type, event_class: type) -> set[str]:
    return {step.__name__ for step in agent_class.get_steps_waiting_for_event(event_class)}


@pytest.mark.parametrize("agent_class", [RAGAgent, ExpertRAGAgent], ids=lambda agent: agent.__name__)
def test_memory_retrieval_is_wired_off_the_query(agent_class):
    on_query = _steps_waiting_for(agent_class, ConversationQueryEvent)
    assert {"retrieve_user_memory_step", "retrieve_organization_memory_step"} <= on_query
    assert "assemble_context_step" in _steps_waiting_for(agent_class, LimitChatHistoryEvent)


@pytest.mark.parametrize("agent_class", [RAGAgent, ExpertRAGAgent], ids=lambda agent: agent.__name__)
def test_memory_storage_is_wired_off_the_query(agent_class):
    assert "store_user_memory_step" in _steps_waiting_for(agent_class, ConversationQueryEvent)
