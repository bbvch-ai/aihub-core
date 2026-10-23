from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.agent.agents.release_notes_agent.ticket_note import TicketNote


class ReleaseNoteBatch(BaseModel):
    """What one model call returns: a note per ticket of the batch, written or translated."""

    notes: Annotated[list[TicketNote], Field(description="One entry per ticket, in the order given.")]

    def by_key(self) -> dict[str, str]:
        """Models sometimes change a key's case or pad it; a key returned twice keeps its first note."""
        notes: dict[str, str] = {}
        for entry in self.notes:
            notes.setdefault(entry.key.strip().upper(), entry.note)
        return notes
