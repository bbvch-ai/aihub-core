from enum import StrEnum


class DocumentAttribute(StrEnum):
    """Attributes shared across document types; each value is also the metadata key the attribute is stored under.

    Shared rather than per type, so one filter such as "dated 2025" works across every type that carries a date.
    What an attribute means for one type is the type's business, see `DocumentTypeDefinition.meanings`.
    """

    DATE = "document_date"
    REFERENCE_NUMBER = "document_reference_number"
    ISSUER = "document_issuer"
    ISSUER_TAX_ID = "document_issuer_tax_id"
    RECIPIENT = "document_recipient"
    PARTIES = "document_parties"
    TOTAL_AMOUNT = "document_total_amount"
    CURRENCY = "document_currency"
    DUE_DATE = "document_due_date"
    PERIOD = "document_period"
    RELATED_REFERENCES = "document_related_references"
