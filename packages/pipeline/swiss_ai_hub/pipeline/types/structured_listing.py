from typing import Annotated

from pydantic import BaseModel, Field


class StructuredListing(BaseModel):
    """Every record a structured source has in scope after a sync, next to what that sync wrote."""

    listed_keys: Annotated[list[str], Field(description="Object key of every record currently in scope.")]
    written_keys: Annotated[list[str], Field(description="Object keys the sync of this run wrote.")]
