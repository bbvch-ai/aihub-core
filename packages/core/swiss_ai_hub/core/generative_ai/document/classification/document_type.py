from enum import StrEnum


class DocumentType(StrEnum):
    """The closed set of document types ingestion classifies into.

    Closed on purpose: a filter over a fixed vocabulary is reliable, an open one the model invents per document is not.
    `OTHER` is everything outside the set: adding a type raises `OTHER`'s version in `DocumentTypeCatalog`, so a
    backfill re-classifies only the documents marked `OTHER`.
    """

    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    OFFER = "offer"
    ORDER = "order"
    DELIVERY_NOTE = "delivery_note"
    RECEIPT = "receipt"
    ACCOUNT_STATEMENT = "account_statement"
    PAYMENT_REMINDER = "payment_reminder"
    CONTRACT = "contract"
    SERVICE_LEVEL_AGREEMENT = "service_level_agreement"
    LETTER = "letter"
    REPORT = "report"
    DOCUMENTATION = "documentation"
    POLICY = "policy"
    EMAIL_THREAD = "email_thread"
    OTHER = "other"
