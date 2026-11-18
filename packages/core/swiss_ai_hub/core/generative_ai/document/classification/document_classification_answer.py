from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType


class DocumentClassificationAnswer(BaseModel):
    """What the model returns: the types, and every attribute's text exactly as the document writes it.

    Every attribute is required *and* nullable, the only shape strict structured output accepts for "not stated";
    without null the model cannot close the object. Values are copied, never converted: reading them is the
    normaliser's job, so a better parser can improve them without another model call. Field names are the attributes'
    metadata keys (`DocumentAttribute`), so the answer maps onto the catalog without a translation table.
    """

    document_type: Annotated[DocumentType, Field(description="The one type that describes the document as a whole")]
    secondary_types: Annotated[
        list[DocumentType],
        Field(description="Further types the document also is, such as an annex of another type; usually empty"),
    ]
    document_date: Annotated[str | None, Field(description="Text of the document's date")]
    document_reference_number: Annotated[str | None, Field(description="Text of the document's own number")]
    document_issuer: Annotated[str | None, Field(description="Name of the issuer")]
    document_issuer_tax_id: Annotated[str | None, Field(description="Text of the issuer's VAT or company number")]
    document_recipient: Annotated[str | None, Field(description="Name of the recipient")]
    document_total_amount: Annotated[str | None, Field(description="Text of the total amount, with its currency")]
    document_currency: Annotated[str | None, Field(description="Text of the total amount's currency")]
    document_due_date: Annotated[str | None, Field(description="Text of the due date or the payment terms")]
    document_period: Annotated[str | None, Field(description="Text of the period or date of supply")]
    document_related_references: Annotated[
        list[str] | None, Field(description="Numbers of other documents this one refers to")
    ]
