from typing import Annotated

from pydantic import BaseModel, Field


class StructuredSyncOutcome(BaseModel):
    """What the sync step hands to the listing step: no configuration and no secret, because step outputs are
    pickled into the Dagster bucket."""

    written_keys: Annotated[list[str], Field(description="Object keys this run wrote, relative to the bucket.")]
    scope_fingerprint: Annotated[
        str, Field(description="Fingerprint of the configuration the sync ran with, re-checked by the listing.")
    ]
