from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.types.ingestion_retry_action import IngestionRetryAction


class IngestionRetryDecision(BaseModel):
    """What the retry sensor does about one failed partition on this tick."""

    action: IngestionRetryAction
    origin_run_id: Annotated[
        str, Field(description="The run that started this failure: the latest one the retry sensor did not request.")
    ]
    failed_attempts: Annotated[int, Field(description="Runs since the origin, the origin included.")]
    retry_number: Annotated[int, Field(description="Which retry under the current pipeline version; 0 unless RETRY.")]
    attempt_started_at: Annotated[
        float | None,
        Field(description="Unix time the latest attempt started; a record changed since is a version it never saw."),
    ] = None
    failed_at: Annotated[float | None, Field(description="Unix time the latest attempt ended.")] = None
