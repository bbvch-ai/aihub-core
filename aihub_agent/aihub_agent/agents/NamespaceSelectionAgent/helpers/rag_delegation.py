"""
RAG agent delegation helpers for NamespaceSelectionAgent.

Provides functions to build events for delegating to RAG agents
(RAGAgent or ExpertRAGAgent) via AgentInTheLoop.
"""

from aihub_lib.nats.events import AgentInTheLoop, KnowledgeSource, RAGWithSourcesStartEvent
from aihub_lib.nats.events.user import UserMessageEvent


def build_rag_start_event(
    original_event: UserMessageEvent,
    selected_sources: list[KnowledgeSource],
    selection_reasoning: str | None = None,
) -> RAGWithSourcesStartEvent:
    """Build RAGWithSourcesStartEvent from user message and selected sources."""
    return RAGWithSourcesStartEvent(
        locale=original_event.locale,
        user=original_event.user,
        messages=original_event.messages,
        files=original_event.files,
        knowledge_sources=selected_sources,
        selection_reasoning=selection_reasoning,
    )


def build_agent_invocation(
    rag_agent_class: str,
    rag_agent_id: str,
    start_event: RAGWithSourcesStartEvent,
) -> AgentInTheLoop.request:
    """Build AgentInTheLoop request for RAG agent delegation."""
    return AgentInTheLoop.invoke(
        agent_class=rag_agent_class,
        agent_id=rag_agent_id,
        start_event=start_event,
    )
