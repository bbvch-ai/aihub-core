from typing import Annotated

from pydantic import BaseModel, Field


class SkippedDataLakeFile(BaseModel):
    """A data lake object the listing left out, kept so the observation can tell the operator why."""

    uri: Annotated[str, Field(description="The URI of the object in the data lake.")]
    reason: Annotated[str, Field(description="Why the object is not ingested.")]
