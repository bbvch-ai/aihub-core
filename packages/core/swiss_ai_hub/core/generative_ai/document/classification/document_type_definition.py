from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType


class DocumentTypeDefinition(BaseModel):
    """One type of the closed set: what it is, how to recognise it, and which attributes apply to it.

    `attributes` decides applicability: an attribute outside it is stored empty whatever the model returns, so a
    filter on it never matches this type. `meanings` overrides an attribute's general meaning only where the general
    one is ambiguous for this type, such as which date of an invoice is its date.
    """

    type: Annotated[DocumentType, Field(description="The type")]
    description: Annotated[str, Field(description="What a document of this type is, as the model is told")]
    excludes: Annotated[
        list[str], Field(description="Documents that resemble this type but are not, as the model is told")
    ] = []
    cue_words: Annotated[list[str], Field(description="Words that often name this type, in de, fr, it and en")] = []
    attributes: Annotated[list[DocumentAttribute], Field(description="Attributes that apply to this type")] = []
    meanings: Annotated[
        dict[DocumentAttribute, str], Field(description="What an attribute means for this type, where it differs")
    ] = {}
    references: Annotated[list[str], Field(description="Sources the type and its attributes were defined from")] = []

    def meaning_of(self, attribute: DocumentAttribute, general_meaning: str) -> str:
        return self.meanings.get(attribute, general_meaning)
