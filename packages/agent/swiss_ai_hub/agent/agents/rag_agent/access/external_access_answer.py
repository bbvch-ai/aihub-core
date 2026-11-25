from typing import Annotated

from pydantic import BaseModel, Field


class ExternalAccessAnswer(BaseModel):
    """What an external access resolver answers: the metadata values the asking user may see."""

    values: Annotated[list[str], Field(description="Metadata values the user may see; empty means nothing.")]
