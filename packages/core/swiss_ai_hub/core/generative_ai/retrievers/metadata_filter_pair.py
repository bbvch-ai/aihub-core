from typing import Annotated

from pydantic import BaseModel, Field


class MetadataFilterPair(BaseModel):
    """A metadata key/value equality filter for RAG retrieval."""

    key: Annotated[str, Field(description="The metadata key to filter on.")]
    value: Annotated[str | int | float | bool, Field(description="The value the metadata key must equal.")]
