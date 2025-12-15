from aihub_lib.nats.events import AgentInTheLoop
from aihub_lib.nats.events.guard import ContextSufficientAcceptEvent


def check_all_retrievals_complete(
    retrieval_responses: list[AgentInTheLoop.response],
    expected_count: int,
) -> bool:
    return len(retrieval_responses) >= expected_count


def check_context_ready_for_history_limit(
    context_sufficient_event: ContextSufficientAcceptEvent | None,
    check_context_sufficiency: bool,
) -> bool:
    if not check_context_sufficiency:
        return True  # Guard was skipped, proceed directly
    return context_sufficient_event is not None
