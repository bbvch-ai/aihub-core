from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import KnowledgeReference
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, KnowledgeCollectionResolver

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)


class KnowledgeDocumentRunScope(BaseModel):
    """What one run's document tools may touch: collections the asking user may read, and the profile's glob."""

    collections: Annotated[list[KnowledgeDocumentCollection], Field(description="The collections of this run.")]
    restricting_glob: Annotated[
        str | None, Field(description="The profile's glob every path must match; none when it sets none.")
    ] = None
    ignored: Annotated[
        list[KnowledgeReference], Field(description="Referenced collections left out, for the answer to name.")
    ] = []

    def pairs(self) -> list[BucketNamespacePair]:
        return [entry.collection for entry in self.collections]

    def identifier_of(self, collection: BucketNamespacePair) -> str:
        entry = next(
            entry for entry in self.collections if KnowledgeCollectionResolver.same(entry.collection, collection)
        )
        return entry.identifier

    def describe(self) -> str:
        """The scope as the model reads it at the top of a tool result, so it never has to guess where it looks."""
        listed = ", ".join(f"{entry.identifier} ({entry.label})" for entry in self.collections)
        restricted = f"; only paths matching '{self.restricting_glob}'" if self.restricting_glob else ""
        return f"Collections: {listed}{restricted}."
