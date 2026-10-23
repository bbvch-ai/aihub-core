from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.agent.agents.release_notes_agent.merged_note import MergedNote


class MergedNotes(BaseModel):
    """What one merge call returns: the entries of one part of a changelog section."""

    entries: Annotated[list[MergedNote], Field(description="Every entry; each note's key appears in exactly one.")]
