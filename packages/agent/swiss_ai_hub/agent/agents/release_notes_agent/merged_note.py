from typing import Annotated

from pydantic import BaseModel, Field


class MergedNote(BaseModel):
    """One entry a model made from related notes, named by the keys of the notes it covers."""

    keys: Annotated[list[str], Field(description="The keys of the notes the entry covers, exactly as given.")]
    text: Annotated[str, Field(description="The entry: one sentence, two at most.")]
