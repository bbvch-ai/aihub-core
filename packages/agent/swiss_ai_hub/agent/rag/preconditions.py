from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    RerankerEvent,
    RetrieverEvent,
)

from swiss_ai_hub.agent.agents.expert_asking_agent.events.answer_stop_event import AnswerStopEvent
from swiss_ai_hub.agent.agents.expert_asking_agent.events.no_answer_stop_event import NoAnswerStopEvent


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
