from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.util.unlanded_partition_retry import UnlandedPartitionRetry


class UnlandedPartitionsReport(BaseModel):
    """Where each partition that did not land stands, so the observation can count it and the sensor can act on it."""

    to_retry: list[UnlandedPartitionRetry] = Field(default_factory=list, description="Due for another attempt now")
    backing_off: list[str] = Field(default_factory=list, description="Retried recently; waiting out the backoff")
    exhausted: list[str] = Field(default_factory=list, description="At the attempt ceiling; retried only on change")
    in_progress: list[str] = Field(default_factory=list, description="Queued or running; left alone")

    @property
    def missing_from_data_lake(self) -> int:
        """Failed or attempted without landing, whatever happens to them next. In-progress partitions are excluded."""
        return len(self.to_retry) + len(self.backing_off) + len(self.exhausted)
