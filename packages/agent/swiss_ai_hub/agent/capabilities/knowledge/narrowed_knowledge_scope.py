from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import KnowledgeReference


class NarrowedKnowledgeScope(BaseModel):
    """The collections a run works on when references may only narrow the profile's, and the references that could
    not narrow it, so the answer can say why they were left out."""

    collections: Annotated[list[KnowledgeReference], Field(description="The collections the run works on.")]
    ignored: Annotated[
        list[KnowledgeReference],
        Field(description="Referenced collections outside the profile's, or ones the asking user may not read."),
    ] = []
