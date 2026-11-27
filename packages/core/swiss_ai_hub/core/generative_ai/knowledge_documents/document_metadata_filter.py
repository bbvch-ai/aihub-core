from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator

from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_attribute_condition import (
    DocumentAttributeCondition,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_verdict import DocumentMetadataVerdict
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange


class DocumentMetadataFilter(BaseModel):
    """The documents a request wants by the type and attributes ingestion classified them with (#2348).

    Matched by code against the stored values, never by a model, and never narrowing on doubt: a document that was not
    classified, or whose value is empty, is unknown and kept, so the extraction's document condition judges it. A
    document counts as a type when that is its primary or one of its secondary types.
    """

    types: Annotated[
        list[DocumentType], Field(description="The document is one of these types; empty when any type counts.")
    ] = []
    conditions: Annotated[
        list[DocumentAttributeCondition], Field(description="Every condition must hold for the document to match.")
    ] = []

    @model_validator(mode="after")
    def _states_something(self) -> Self:
        if not self.types and not self.conditions:
            raise ValueError("a metadata filter needs a type or a condition")
        return self

    @classmethod
    def of(
        cls, types: list[DocumentType], conditions: Annotated[list[DocumentAttributeCondition], "As a model wrote them"]
    ) -> Self | None:
        """The filter of the readable conditions, or None when nothing readable is left."""
        readable = [condition for condition in (c.readable() for c in conditions) if condition is not None]
        return cls(types=list(dict.fromkeys(types)), conditions=readable) if types or readable else None

    def verdict(
        self,
        document: KnowledgeDocumentSummary,
        period: Annotated[PathDateRange | None, "The request's period, matched against the document's own date"] = None,
    ) -> DocumentMetadataVerdict:
        """The request's period applies to the document's own date as well as to its path. A type without such a date
        is unknown for it rather than excluded: the period is the request's, not a condition on that type. `OTHER` and
        a type the catalog no longer holds count as unclassified: a backfill re-classifies them once a type is added."""
        if document.document_type not in DocumentType or document.document_type == DocumentType.OTHER:
            return DocumentMetadataVerdict.UNKNOWN
        verdicts = [self._type_verdict(document), *(condition.verdict(document) for condition in self.conditions)]
        if period is not None:
            dated = DocumentAttributeCondition(
                attribute=DocumentAttribute.DATE,
                at_least=period.start.isoformat() if period.start else None,
                at_most=period.end.isoformat() if period.end else None,
            )
            verdicts.append(dated.verdict(document, inapplicable=DocumentMetadataVerdict.UNKNOWN))
        return DocumentMetadataVerdict.combined(verdicts)

    def _type_verdict(self, document: KnowledgeDocumentSummary) -> DocumentMetadataVerdict:
        if not self.types:
            return DocumentMetadataVerdict.MATCH
        types = {document.document_type, *document.document_types}
        return DocumentMetadataVerdict.MATCH if types & set(self.types) else DocumentMetadataVerdict.EXCLUDED
