from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.jira import JiraTicket

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_section import ChangelogSection


class ReleaseNote(BaseModel):
    """One changelog bullet: a ticket and the note written for it."""

    key: Annotated[str, Field(description="Issue key, e.g. ENG-12.")]
    url: Annotated[str, Field(description="Where a reader opens the ticket.")]
    project: Annotated[str, Field(description="Key of the ticket's project.")]
    number: Annotated[int, Field(description="The ticket's number within its project.")]
    section: Annotated[ChangelogSection, Field(description="The changelog section the ticket's type belongs to.")]
    summary: Annotated[str, Field(description="The ticket's summary, used when no note could be written.")]
    note: Annotated[str, Field(description="The text of the bullet.")]
    fallback: Annotated[
        bool, Field(description="Whether the note stands in for one the model did not write or translate.")
    ] = False

    @classmethod
    def from_ticket(
        cls,
        ticket: Annotated[JiraTicket, "The ticket the note is written for"],
        note: Annotated[str | None, "The model's note; None falls back to the ticket's summary"],
    ) -> Self:
        written = (note or "").strip()
        return cls(
            key=ticket.key,
            url=ticket.url,
            project=ticket.project,
            number=ticket.number,
            section=ChangelogSection.of_issue_type(ticket.issue_type),
            summary=ticket.summary,
            note=written or ticket.summary,
            fallback=not written,
        )
