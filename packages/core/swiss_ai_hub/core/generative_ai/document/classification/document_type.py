from enum import StrEnum


class DocumentType(StrEnum):
    """The closed set of document types ingestion classifies into.

    Closed on purpose: a filter over a fixed vocabulary is reliable, an open one the model invents per document is not.
    `OTHER` is everything outside the set: adding a type raises `OTHER`'s version in `DocumentTypeCatalog`, so a
    backfill re-classifies only the documents marked `OTHER`.
    """

    INVOICE = "invoice"
    OTHER = "other"
