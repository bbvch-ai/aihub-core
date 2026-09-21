from swiss_ai_hub.pipeline.sensors.nats.observation_run_decider import DEBOUNCE_SECONDS, ObservationRunDecider
from swiss_ai_hub.pipeline.sensors.nats.observation_sensor_cursor import ObservationSensorCursor

_NOW = 1_700_000_000.0


def _reason(cursor: ObservationSensorCursor, now: float = _NOW, **overrides) -> str | None:
    return ObservationRunDecider.reason_to_request(
        cursor=cursor,
        now=now,
        truncation_run_id=overrides.get("truncation_run_id"),
        requested_run_missing=overrides.get("requested_run_missing", False),
    )


class TestDebounce:
    def test_idle_cursor_requests_nothing(self) -> None:
        assert _reason(ObservationSensorCursor()) is None

    def test_events_younger_than_the_debounce_are_held(self) -> None:
        cursor = ObservationSensorCursor(pending_events=3, first_pending_at=_NOW - (DEBOUNCE_SECONDS - 1))

        assert _reason(cursor) is None

    def test_events_older_than_the_debounce_are_requested(self) -> None:
        cursor = ObservationSensorCursor(pending_events=3, first_pending_at=_NOW - DEBOUNCE_SECONDS)

        assert _reason(cursor) is not None

    def test_a_large_backlog_still_waits_for_the_debounce(self) -> None:
        """Single-flight, not the debounce, is what bounds the run count, so there is no
        pending-count escape hatch to trip here."""
        cursor = ObservationSensorCursor(pending_events=5_000, first_pending_at=_NOW)

        assert _reason(cursor) is None


class TestReArmTriggers:
    def test_followup_armed_requests_immediately(self) -> None:
        """The snapshot-race guard: events seen while a run was in flight owe one follow-up,
        regardless of how recently they arrived."""
        cursor = ObservationSensorCursor(pending_events=1, first_pending_at=_NOW, followup_armed=True)

        assert _reason(cursor) == "events arrived while an observation was in flight"

    def test_unhandled_truncation_requests_a_run(self) -> None:
        assert _reason(ObservationSensorCursor(), truncation_run_id="run-abc") is not None

    def test_already_handled_truncation_does_not_request_again(self) -> None:
        cursor = ObservationSensorCursor(handled_truncation="run-abc")

        assert _reason(cursor, truncation_run_id="run-abc") is None

    def test_a_newer_truncating_run_requests_again(self) -> None:
        cursor = ObservationSensorCursor(handled_truncation="run-abc")

        assert _reason(cursor, truncation_run_id="run-def") is not None

    def test_requested_run_that_never_launched_is_requested_again(self) -> None:
        cursor = ObservationSensorCursor(requested_run_key="bucket_to_db_seq_1_r0")

        assert _reason(cursor, requested_run_missing=True) is not None
