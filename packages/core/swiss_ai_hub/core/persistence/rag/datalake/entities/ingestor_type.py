from enum import StrEnum
from typing import Self


class IngestorType(StrEnum):
    """The platform's own routing tokens for which deployed ingestion pipeline owns a knowledge database.

    ``document_ingestion`` is the shipped pipeline; it registers itself like any custom ingestor, so the API
    learns about it from its registration record rather than from this enum. The others are routing guards
    only, never offered to users.

    ``UNASSIGNED`` is the field default, and exists so that rows written before this field was
    introduced — which have no ``ingestor`` key, and for which MongoEngine therefore applies the
    field default on load — are owned by no ingestion pipeline. Defaulting to
    ``DOCUMENT_INGESTION`` instead would make every pre-existing knowledge database in an upgraded
    deployment get claimed and re-ingested by the document ingestion pipeline alongside the
    deploy-bound pipeline that already owns it.
    """

    UNASSIGNED = "unassigned"
    DEFAULT_RAG = "default_rag"
    SHARED_RAG = "shared_rag"
    DOCUMENT_INGESTION = "document_ingestion"

    @classmethod
    def legacy(cls) -> list[Self]:
        """Tokens no pipeline may register.

        ``default_rag`` and ``shared_rag`` are bound to one bucket by env var at deploy time, so a
        database assigned to either would never be ingested — they exist only to mark the legacy
        buckets for the routing guard. ``unassigned`` means "no ingestion pipeline owns this".
        """
        return [cls.UNASSIGNED, cls.DEFAULT_RAG, cls.SHARED_RAG]
