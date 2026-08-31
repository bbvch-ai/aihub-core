from typing import Annotated, Self

from pydantic import BaseModel, Field, ValidationError

from swiss_ai_hub.pipeline.sensors.nats.observation_sensor_cursor import ObservationSensorCursor


class PerBucketObservationSensorCursor(BaseModel):
    """The observation state of every knowledge database one sensor serves, in Dagster's single cursor slot.

    A configurable pipeline has one sensor for many databases, but debounce, follow-up and truncation
    state are per database — a shared cursor would let one busy database keep resetting another's clock.
    """

    buckets: Annotated[
        dict[str, ObservationSensorCursor],
        Field(default_factory=dict, description="Per-bucket observation state, keyed by bucket name"),
    ]

    @classmethod
    def from_cursor(cls, cursor: Annotated[str | None, "Raw cursor string Dagster persisted"]) -> Self:
        """Falls back to empty state rather than raising, so a cursor written by an older version of
        this model cannot wedge the sensor into permanent tick failures."""
        if not cursor:
            return cls()
        try:
            return cls.model_validate_json(cursor)
        except ValidationError:
            return cls()

    def for_bucket(self, bucket_name: Annotated[str, "Knowledge database's bucket"]) -> ObservationSensorCursor:
        return self.buckets.setdefault(bucket_name, ObservationSensorCursor())

    def prune(self, known_buckets: Annotated[set[str], "Buckets that still exist and are owned"]) -> None:
        """Drops state for torn-down databases, which would otherwise grow the cursor without bound."""
        for bucket_name in set(self.buckets) - known_buckets:
            del self.buckets[bucket_name]
