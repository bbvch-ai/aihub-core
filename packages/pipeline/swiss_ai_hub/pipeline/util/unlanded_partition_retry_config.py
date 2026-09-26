from datetime import timedelta

from dagster import AssetKey
from pydantic import BaseModel, ConfigDict, Field


class UnlandedPartitionRetryConfig(BaseModel):
    """What to re-request and how often, shared by the observation that reports the gap and the sensor that closes it.

    Kept apart from any one pipeline's settings so the ingestion assets can reuse it (#1813).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    asset_key: AssetKey = Field(description="Partitioned asset whose failed or unlanded partitions are re-requested")
    retry_job_name: str = Field(description="Job that re-requests them; its runs are what count as attempts")
    max_attempts: int = Field(ge=0, description="Re-requests per partition since its last successful materialization")
    base_delay: timedelta = Field(description="Wait after the first re-request; doubles with every further attempt")
