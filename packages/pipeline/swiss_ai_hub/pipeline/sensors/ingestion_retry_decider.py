from typing import Annotated

from swiss_ai_hub.pipeline.types.ingestion_attempt import IngestionAttempt
from swiss_ai_hub.pipeline.types.ingestion_retry_action import IngestionRetryAction
from swiss_ai_hub.pipeline.types.ingestion_retry_decision import IngestionRetryDecision


class IngestionRetryDecider:
    """Decides, from a failed partition's run history alone, whether to retry it now, later, or not at all.

    A failure starts with the latest run the retry sensor did not request: the automation run a new or changed file
    triggered, or a run launched by hand. Every retry since then belongs to that failure, and its budget is counted
    per pipeline version, so a release that fixes the cause retries every document the bug left failed.
    """

    @staticmethod
    def decide(
        history: Annotated[list[IngestionAttempt], "Runs of the partition, newest first"],
        pipeline_version: str,
        max_retries: int,
        backoff_seconds: float,
        now: float,
    ) -> IngestionRetryDecision | None:
        """None while a run of the partition is still going, or when it has no run at all."""
        if not history or not all(attempt.is_finished for attempt in history):
            return None

        failure = IngestionRetryDecider._runs_of_latest_failure(history)
        retries_of_this_version = sum(
            attempt.is_retry and attempt.pipeline_version == pipeline_version for attempt in failure
        )
        latest = history[0]

        if retries_of_this_version >= max_retries:
            action = IngestionRetryAction.GIVE_UP
        elif latest.end_time is not None and now < latest.end_time + backoff_seconds:
            action = IngestionRetryAction.WAIT
        else:
            action = IngestionRetryAction.RETRY

        return IngestionRetryDecision(
            action=action,
            origin_run_id=failure[-1].run_id,
            failed_attempts=len(failure),
            retry_number=retries_of_this_version + 1 if action is IngestionRetryAction.RETRY else 0,
            attempt_started_at=latest.start_time,
            failed_at=latest.end_time,
        )

    @staticmethod
    def _runs_of_latest_failure(history: list[IngestionAttempt]) -> list[IngestionAttempt]:
        """The runs from the newest back to the latest one not requested by the retry sensor, both included.

        Only the window the caller fetched is seen; if every run in it is a retry, the oldest one stands in for the
        origin, which keeps the run key stable while that window does not move.
        """
        for index, attempt in enumerate(history):
            if not attempt.is_retry:
                return history[: index + 1]
        return history
