from typing import Annotated

from swiss_ai_hub.pipeline.sensors.nats.observation_sensor_cursor import ObservationSensorCursor

DEBOUNCE_SECONDS = 30


class ObservationRunDecider:
    """Decides whether a tick with no observation in flight should request one.

    Kept free of NATS and Dagster so the branching can be tested directly. Firing eagerly is safe
    because the single-flight guard, not this debounce, is what bounds the number of runs.
    """

    @staticmethod
    def reason_to_request(
        cursor: Annotated[ObservationSensorCursor, "State carried over from previous ticks"],
        now: Annotated[float, "Current wall clock, injected so tests stay deterministic"],
        truncation_run_id: Annotated[str | None, "Latest run that truncated the partition set, if any"],
        requested_run_missing: Annotated[bool, "A previously requested run key never became a run"],
    ) -> str | None:
        """The reason to request a run, or None to keep waiting."""
        if cursor.followup_armed:
            return "events arrived while an observation was in flight"

        if truncation_run_id and truncation_run_id != cursor.handled_truncation:
            return f"run {truncation_run_id} truncated the partition set"

        if requested_run_missing:
            return f"requested run key {cursor.requested_run_key} never launched"

        waited_long_enough = cursor.first_pending_at is not None and now - cursor.first_pending_at >= DEBOUNCE_SECONDS
        if cursor.pending_events and waited_long_enough:
            return f"{cursor.pending_events} event(s) waited {DEBOUNCE_SECONDS}s"

        return None
