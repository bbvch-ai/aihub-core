from enum import StrEnum
from typing import Self


class IngestorType(StrEnum):
    """Identifies which deployed ingestion pipeline owns a knowledge database.

    Used as a routing guard: the single ``rag`` pipeline reads this off each
    ``BucketEntity`` to decide which buckets it ingests, so it can coexist with the legacy
    per-bucket ``default_rag`` / ``shared_rag`` deployments without double-processing them.

    ``UNASSIGNED`` is the field default, and exists so that rows written before this field was
    introduced — which have no ``ingestor`` key, and for which MongoEngine therefore applies the
    field default on load — are owned by no RAG pipeline. Defaulting to
    ``RAG`` instead would make every pre-existing knowledge database in an upgraded
    deployment get claimed and re-ingested by the RAG pipeline alongside the deploy-bound
    pipeline that already owns it.
    """

    UNASSIGNED = "unassigned"
    DEFAULT_RAG = "default_rag"
    SHARED_RAG = "shared_rag"
    RAG = "rag"

    @classmethod
    def selectable(cls) -> list[Self]:
        """Ingestors a user may assign when creating a knowledge database.

        ``default_rag`` and ``shared_rag`` are bound to one bucket by env var at deploy time, so a
        database assigned to either would never be ingested — they exist only to mark the legacy
        buckets for the routing guard. ``unassigned`` means "no RAG pipeline owns this"
        and is likewise not something a user picks.
        """
        return [cls.RAG]
