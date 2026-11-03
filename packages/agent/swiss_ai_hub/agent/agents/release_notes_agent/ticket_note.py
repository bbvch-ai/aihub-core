from typing import Annotated

from pydantic import BaseModel, Field


class TicketNote(BaseModel):
    """The note a model wrote for one ticket, named by the key it was given."""

    key: Annotated[str, Field(description="The ticket key exactly as given, e.g. ENG-12.")]
    note: Annotated[str, Field(description="One or two sentences for the release notes.")]
