"""A request settled by its timeout, or a delegation answered by a failure, is no longer open, and a timeout shows."""

from swiss_ai_hub.api.routes.thread.dto.statistics.intermediate_display_stats import IntermediateDisplayStats


def _stats(**counts: int) -> IntermediateDisplayStats:
    stats = IntermediateDisplayStats(display_id="display")
    stats.update_from_run_data(counts)
    return stats


def test_a_timed_out_question_is_settled_and_reported():
    stats = _stats(hitl_request_events=1, hitl_timeout_events=1)

    assert not stats.open_hitl
    assert stats.has_timeouts


def test_an_unanswered_question_without_timeout_stays_open():
    stats = _stats(hitl_request_events=2, hitl_response_events=1)

    assert stats.open_hitl
    assert not stats.has_timeouts


def test_delegations_answered_by_a_response_a_failure_or_a_timeout_are_all_settled():
    stats = _stats(aitl_request_events=3, aitl_response_events=2, aitl_timeout_events=1)

    assert not stats.open_aitl
