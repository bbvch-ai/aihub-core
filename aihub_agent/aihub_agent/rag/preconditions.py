"""
Shared precondition logic functions for RAG-based agents.

These are regular functions containing the precondition logic.
Each agent should define its own @precondition() decorated functions
that call these shared logic functions with the appropriate config types.
"""

from aihub_lib.nats.events import AgentInTheLoop
from aihub_lib.nats.events.guard import ContextSufficientAcceptEvent
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent

from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.RagAgent.events.ExpertAnswerContextEvent import ExpertAnswerContextEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent


def check_reranking_enabled(event: RetrieverEvent, reranking_enabled: bool) -> bool:
    """Check if reranking step should run."""
    return isinstance(event, RetrieverEvent) and reranking_enabled


def check_reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, reranking_enabled: bool) -> bool:
    """Ensure ordering only happens after reranking is complete (or if disabled)."""
    if not reranking_enabled:
        return isinstance(event, RetrieverEvent)
    return isinstance(event, RerankerEvent)


def check_is_answer_response(event: AgentInTheLoop.response) -> bool:
    """Check if agent-in-the-loop response is a successful answer."""
    return isinstance(event.stop_event, AnswerStopEvent)


def check_is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Check if agent-in-the-loop response is an unsuccessful answer."""
    return isinstance(event.stop_event, NoAnswerStopEvent)


def check_context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """Check if context is ready for history limiting (RAGAgent version)."""
    return context_sufficient_event is not None


def check_context_ready_for_history_limit_with_expert(
    context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """Check if context is ready for history limiting (ExpertRAGAgent version)."""
    if isinstance(context_event, ExpertAnswerContextEvent):
        return True
    return context_sufficient_event is not None
