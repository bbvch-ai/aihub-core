from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    ContextSufficientAcceptEvent,
    RerankerEvent,
    RetrieverEvent,
)

from swiss_ai_hub.agent.agents.expert_asking_agent.events.answer_stop_event import AnswerStopEvent
from swiss_ai_hub.agent.agents.expert_asking_agent.events.no_answer_stop_event import NoAnswerStopEvent
from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent


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


def check_context_ready_for_history_limit_with_expert(
    context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """Check if context is ready for history limiting (ExpertRAGAgent version)."""
    if isinstance(context_event, ExpertAnswerContextEvent):
        return True
    return context_sufficient_event is not None
