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
    """
    Logic to check if reranking step should run.

    Args:
        event: The retriever event
        reranking_enabled: Whether reranking is enabled in config

    Returns:
        True if reranking should run
    """
    return isinstance(event, RetrieverEvent) and reranking_enabled


def check_reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, reranking_enabled: bool) -> bool:
    """
    Logic to ensure ordering only happens after reranking is complete (or if disabled).

    Args:
        event: The retriever or reranker event
        reranking_enabled: Whether reranking is enabled in config

    Returns:
        True if ordering step should run
    """
    if not reranking_enabled:
        return isinstance(event, RetrieverEvent)
    return isinstance(event, RerankerEvent)


def check_is_answer_response(event: AgentInTheLoop.response) -> bool:
    """
    Logic to check if agent-in-the-loop response is a successful answer.

    Args:
        event: The agent-in-the-loop response event

    Returns:
        True if the response contains an AnswerStopEvent
    """
    return isinstance(event.stop_event, AnswerStopEvent)


def check_is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """
    Logic to check if agent-in-the-loop response is an unsuccessful answer.

    Args:
        event: The agent-in-the-loop response event

    Returns:
        True if the response contains a NoAnswerStopEvent
    """
    return isinstance(event.stop_event, NoAnswerStopEvent)


def check_context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """
    Logic to check if context is ready for history limiting (RAGAgent version).

    For RAGAgent (no expert flow), we need ContextSufficientAcceptEvent.

    Args:
        context_event: The context event (InOrderNodeCombinerEvent)
        context_sufficient_event: The context sufficient event (optional)

    Returns:
        True if history limiting step should run
    """
    return context_sufficient_event is not None


def check_context_ready_for_history_limit_with_expert(
    context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """
    Logic to check if context is ready for history limiting (ExpertRAGAgent version).

    For ExpertRAGAgent, we allow either:
    - ExpertAnswerContextEvent (expert flow), OR
    - InOrderNodeCombinerEvent with ContextSufficientAcceptEvent (normal RAG flow)

    Args:
        context_event: The context event (InOrderNodeCombinerEvent or ExpertAnswerContextEvent)
        context_sufficient_event: The context sufficient event (optional)

    Returns:
        True if history limiting step should run
    """
    if isinstance(context_event, ExpertAnswerContextEvent):
        return True
    return context_sufficient_event is not None
