"""
Shared RAG utilities for RAGAgent and ExpertRAGAgent.

This module contains reusable step functions and precondition logic used by RAG-based agents.
"""

from aihub_agent.rag.preconditions import (
    check_context_ready_for_history_limit,
    check_context_ready_for_history_limit_with_expert,
    check_is_answer_response,
    check_is_no_answer_response,
    check_reranking_complete_or_disabled,
    check_reranking_enabled,
)
from aihub_agent.rag.step_functions import (
    build_llm_response_messages,
    format_expert_conversation,
    get_nodes_from_event,
    get_query_from_event,
)

__all__ = [
    # Precondition logic functions (to be used inside @precondition decorated functions)
    "check_reranking_enabled",
    "check_reranking_complete_or_disabled",
    "check_is_answer_response",
    "check_is_no_answer_response",
    "check_context_ready_for_history_limit",
    "check_context_ready_for_history_limit_with_expert",
    # Step functions
    "get_query_from_event",
    "get_nodes_from_event",
    "format_expert_conversation",
    "build_llm_response_messages",
]
