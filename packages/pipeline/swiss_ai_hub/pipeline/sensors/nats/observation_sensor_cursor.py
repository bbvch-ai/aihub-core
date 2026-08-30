from typing import Annotated, Self

from pydantic import BaseModel, Field, ValidationError


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
