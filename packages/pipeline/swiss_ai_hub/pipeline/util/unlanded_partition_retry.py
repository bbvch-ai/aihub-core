from hashlib import md5

from pydantic import BaseModel, Field


class UnlandedPartitionRetry(BaseModel):
    """One partition due for another attempt."""

    partition_key: str
    attempt: int = Field(ge=1, description="Attempt number since the partition's last successful materialization")
    run_number: int = Field(ge=0, description="Retry runs this partition has had in total, across every reset")

    @property
    def run_key(self) -> str:
        """Numbered by the total rather than by ``attempt``, because Dagster deduplicates run keys forever and
        ``attempt`` restarts at 1 after a success. Composite keys contain ``|`` and ``%``, hence the hash."""
        digest = md5(self.partition_key.encode(), usedforsecurity=False).hexdigest()
        return f"retry_{digest}_{self.run_number}"
