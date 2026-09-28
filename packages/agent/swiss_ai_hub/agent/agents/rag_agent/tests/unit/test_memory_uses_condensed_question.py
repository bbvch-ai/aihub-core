"""Memory operations use the turn's query, never the RAG-augmented prompt (#1753).

Chat clients running full-context RAG inline whole documents into the last user message. These tests pin
the structural guarantee on every RAG blueprint: memory is recalled off the contextualized turn (search
embeds the condensed question, not documents), and the storage payload is the query plus the answer, which
`capabilities/tests/test_memory_capability.py` pins on `Memory.remember`.
"""

import pytest
from swiss_ai_hub.core.events.agent import ConversationContextualizedEvent

from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent


@pytest.mark.parametrize("agent_class", [RAGAgent, ExpertRAGAgent], ids=lambda agent: agent.__name__)
def test_memory_is_recalled_off_the_contextualized_turn(agent_class):
    on_turn = {step.__name__ for step in agent_class.get_steps_waiting_for_event(ConversationContextualizedEvent)}
    assert "recall_memory_step" in on_turn
