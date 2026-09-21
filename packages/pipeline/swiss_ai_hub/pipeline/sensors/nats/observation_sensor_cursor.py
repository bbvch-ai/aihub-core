from typing import Annotated, Self

from pydantic import BaseModel, Field, ValidationError

from swiss_ai_hub.pipeline.sensors.nats.consumed_event_batch import ConsumedEventBatch


class ObservationSensorCursor(BaseModel):
    """State the observation sensor carries between ticks, serialized into Dagster's sensor cursor.

    Dagster gives a sensor one opaque string of memory. Everything the sensor cannot re-derive from
    the event stream on the next tick lives here: how long a burst has been waiting, whether a
    follow-up run is owed, and which truncating run it has already answered.
    """

    pending_events: Annotated[int, Field(description="Events waiting for a run to be requested")] = 0
    first_pending_at: Annotated[
        float | None, Field(description="When the oldest waiting event arrived; drives the debounce")
    ] = None
    max_sequence: Annotated[int, Field(description="Highest stream sequence seen, survives debounce holds")] = 0
    requested_run_key: Annotated[
        str | None, Field(description="Run key of the last request, to detect one the daemon never launched")
    ] = None
    followup_armed: Annotated[
        bool, Field(description="Events arrived while a run was in flight, so one follow-up is owed")
    ] = False
    handled_truncation: Annotated[
        str | None, Field(description="Run id of the truncating run already re-armed for")
    ] = None
    rearm_count: Annotated[int, Field(description="Distinguishes run keys of re-arms carrying no new events")] = 0

    @classmethod
    def from_cursor(cls, cursor: Annotated[str | None, "Raw cursor string Dagster persisted"]) -> Self:
        """Falls back to empty state rather than raising, so a cursor written by an older
        version of this model cannot wedge the sensor into permanent tick failures."""
        if not cursor:
            return cls()
        try:
            return cls.model_validate_json(cursor)
        except ValidationError:
            return cls()

    def absorb(
        self,
        batch: Annotated[ConsumedEventBatch, "Events drained from JetStream this tick"],
        now: Annotated[float, "Current wall clock, injected so tests stay deterministic"],
    ) -> None:
        """Folds a drained batch into the debounce state, starting the clock on the first event."""
        if not batch.count:
            return
        self.pending_events += batch.count
        if self.first_pending_at is None:
            self.first_pending_at = now
        self.max_sequence = max(self.max_sequence, batch.max_sequence)

    def arm_followup(self, batch: Annotated[ConsumedEventBatch, "Events drained this tick"]) -> None:
        """A run already in flight may have listed the bucket before these files landed, so it
        cannot be trusted to cover them; owe exactly one follow-up instead."""
        self.followup_armed = self.followup_armed or bool(batch.count)

    def next_run_key(self, pipeline_id: Annotated[str, "Source-to-target identifier of the pipeline"]) -> str:
        """Guards on the key itself, not on an empty batch: a batch whose sequences were all seen
        before leaves ``max_sequence`` unchanged too, which happens when the stream is recreated or
        restored and its sequence numbering restarts. Reusing the key last requested would let
        Dagster's idempotence check drop the very run being re-armed."""
        run_key = f"{pipeline_id}_seq_{self.max_sequence}_r{self.rearm_count}"
        if run_key != self.requested_run_key:
            return run_key
        self.rearm_count += 1
        return f"{pipeline_id}_seq_{self.max_sequence}_r{self.rearm_count}"

    def mark_requested(
        self,
        run_key: Annotated[str, "Run key just handed to Dagster"],
        truncation_run_id: Annotated[str | None, "Truncating run this request answers, if any"],
    ) -> None:
        """Clears the debounce state so the next tick starts from a clean slate."""
        self.pending_events = 0
        self.first_pending_at = None
        self.followup_armed = False
        self.handled_truncation = truncation_run_id or self.handled_truncation
        self.requested_run_key = run_key
