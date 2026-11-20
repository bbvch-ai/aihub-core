"""A failed document is retried a bounded number of times per pipeline version, a backoff apart."""

from swiss_ai_hub.pipeline.sensors.ingestion_retry_decider import IngestionRetryDecider
from swiss_ai_hub.pipeline.types.ingestion_attempt import IngestionAttempt
from swiss_ai_hub.pipeline.types.ingestion_retry_action import IngestionRetryAction

_VERSION = "0.327.0"
_BACKOFF = 600.0
_NOW = 10_000.0


def _automation_run(run_id: str = "origin", end_time: float = 1_000.0) -> IngestionAttempt:
    return IngestionAttempt(run_id=run_id, is_retry=False, is_finished=True, end_time=end_time)


def _retry(run_id: str, version: str = _VERSION, end_time: float = 2_000.0) -> IngestionAttempt:
    return IngestionAttempt(run_id=run_id, is_retry=True, pipeline_version=version, is_finished=True, end_time=end_time)


def _decide(*history: IngestionAttempt, max_retries: int = 3):
    return IngestionRetryDecider.decide(list(history), _VERSION, max_retries, _BACKOFF, now=_NOW)


def test_a_failure_is_retried_without_its_file_changing() -> None:
    decision = _decide(_automation_run())

    assert decision.action is IngestionRetryAction.RETRY
    assert decision.retry_number == 1
    assert decision.origin_run_id == "origin"
    assert decision.failed_attempts == 1


def test_a_retry_waits_for_the_backoff_after_the_latest_attempt() -> None:
    decision = _decide(_automation_run(end_time=_NOW - _BACKOFF + 1))

    assert decision.action is IngestionRetryAction.WAIT


def test_a_retry_is_due_once_the_backoff_has_passed() -> None:
    decision = _decide(_automation_run(end_time=_NOW - _BACKOFF))

    assert decision.action is IngestionRetryAction.RETRY


def test_a_document_that_keeps_failing_is_given_up_after_its_retries() -> None:
    decision = _decide(_retry("r3"), _retry("r2"), _retry("r1"), _automation_run())

    assert decision.action is IngestionRetryAction.GIVE_UP
    assert decision.failed_attempts == 4
    assert decision.retry_number == 0


def test_a_new_pipeline_version_retries_a_document_the_old_one_gave_up() -> None:
    """The release that fixes a bug is enough to recover the documents it left failed, with no re-upload."""
    old = "0.326.0"
    decision = _decide(_retry("r3", old), _retry("r2", old), _retry("r1", old), _automation_run())

    assert decision.action is IngestionRetryAction.RETRY
    assert decision.retry_number == 1
    assert decision.failed_attempts == 4


def test_a_new_failure_of_a_changed_file_gets_its_own_budget_and_origin() -> None:
    """Retries of an earlier failure belong to that failure: an automation run after them starts a new one."""
    decision = _decide(_automation_run("new"), _retry("r3"), _retry("r2"), _retry("r1"), _automation_run("old"))

    assert decision.action is IngestionRetryAction.RETRY
    assert decision.origin_run_id == "new"
    assert decision.retry_number == 1


def test_the_decision_carries_when_the_latest_attempt_started_and_ended() -> None:
    latest = IngestionAttempt(run_id="r1", is_retry=True, is_finished=True, start_time=1_900.0, end_time=2_000.0)

    decision = _decide(latest, _automation_run())

    assert (decision.attempt_started_at, decision.failed_at) == (1_900.0, 2_000.0)


def test_nothing_is_decided_while_a_run_of_the_partition_is_still_going() -> None:
    running = IngestionAttempt(run_id="running", is_retry=False, is_finished=False)

    assert _decide(running, _automation_run()) is None


def test_nothing_is_decided_for_a_partition_without_runs() -> None:
    assert _decide() is None


def test_no_retries_configured_gives_up_at_once() -> None:
    assert _decide(_automation_run(), max_retries=0).action is IngestionRetryAction.GIVE_UP
