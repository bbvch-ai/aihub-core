"""Shared precondition logic for RAG workflows.

These are plain helper functions, NOT decorated preconditions.
Use these in @precondition() decorated functions within agent files.
"""

from aihub_lib.nats.events import AgentInTheLoop
from aihub_lib.nats.events.guard import ContextSufficientAcceptEvent


def check_all_retrievals_complete(
    retrieval_responses: list[AgentInTheLoop.response],
    expected_count: int,
) -> bool:
    """Helper to check if all retrieval agents have completed."""
    return len(retrieval_responses) >= expected_count


def check_context_ready_for_history_limit(
    context_sufficient_event: ContextSufficientAcceptEvent | None,
) -> bool:
    """Helper to check if context is ready for history limiting."""
    return context_sufficient_event is not None
