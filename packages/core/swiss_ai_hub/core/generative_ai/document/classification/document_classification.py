from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.document_type_catalog import DocumentTypeCatalog
from swiss_ai_hub.core.generative_ai.document.classification.document_value_normalizer import DocumentValueNormalizer
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    DOCUMENT_CLASSIFICATION_VERSION,
    DOCUMENT_NORMALIZER_VERSION,
    DOCUMENT_TYPE,
    DOCUMENT_TYPES,
)


class DocumentClassification(BaseModel):
    """A document's type, the further types it also is, and its attributes as stored.

    The primary type owns the attributes; secondary types are labels only, so a document that is both an invoice and a
    delivery note is found by either type while its date stays the invoice's date. `document_types` lists the primary
    type first, so a filter on the list finds both.
    """

    document_type: Annotated[DocumentType, Field(description="The type that describes the document as a whole")]
    document_types: Annotated[list[DocumentType], Field(description="Every type of the document, primary first")]
    values: Annotated[dict[str, Any], Field(description="Stored attribute keys and values; None where unknown")]

    @classmethod
    def from_answer(cls, answer: DocumentClassificationAnswer, document_text: str) -> Self:
        secondary = [
            document_type
            for document_type in dict.fromkeys(answer.secondary_types)
            if document_type not in (answer.document_type, DocumentType.OTHER)
        ]
        return cls(
            document_type=answer.document_type,
            document_types=[answer.document_type, *secondary[: DocumentTypeCatalog.MAX_SECONDARY_TYPES]],
            values=DocumentValueNormalizer.normalize(answer.document_type, answer, document_text),
        )

    def to_metadata(self) -> dict[str, Any]:
        """The metadata to store on the document and every node, stamped with the versions it was produced with."""
        return {
            DOCUMENT_TYPE: self.document_type.value,
            DOCUMENT_TYPES: [document_type.value for document_type in self.document_types],
            DOCUMENT_CLASSIFICATION_VERSION: DocumentTypeCatalog.VERSION,
            DOCUMENT_NORMALIZER_VERSION: DocumentValueNormalizer.VERSION,
            **self.values,
        }
